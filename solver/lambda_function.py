import os
import logging
import boto3
import json
from helpers import _extract_text_from_response

model_id = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")

bedrock = boto3.client("bedrock-runtime")

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Change to INFO in production


def lambda_handler(event, context):
    """
    AWS Lambda to solve a crossword puzzle using Amazon Q for clue solving.
    """

    logger.info("Received event: %s", json.dumps(event))

    try:
        # Parse the crossword inputs
        clues = event.get("clues", {})
        if isinstance(clues, str):
            clues = json.loads(clues)

        grid_data = event.get("grid_data", {})
        if isinstance(grid_data, str):
            grid_data = json.loads(grid_data)

        across_clues = clues.get("across", [])
        down_clues = clues.get("down", [])

        logger.info("Parsed %d across clues and %d down clues", len(across_clues), len(down_clues))

        grid_matrix = grid_data.get("grid_matrix", [])
        across_positions = grid_data.get("across_clues", [])
        down_positions = grid_data.get("down_clues", [])

        logger.info("Grid matrix size: %dx%d", len(grid_matrix), len(grid_matrix[0]) if grid_matrix else 0)
        logger.info("Across positions: %s", across_positions)
        logger.info("Down positions: %s", down_positions)

        # ---- Sanity checks ----
        if len(across_clues) != len(across_positions):
            raise ValueError(
                f"Across clues mismatch: {len(across_clues)} clues vs {len(across_positions)} positions"
            )
        if len(down_clues) != len(down_positions):
            raise ValueError(
                f"Down clues mismatch: {len(down_clues)} clues vs {len(down_positions)} positions"
            )

        # Prepare empty solution grid
        solution_grid = [["" for _ in row] for row in grid_matrix]
        logger.info("Initialized empty solution grid")

        # ---- Across clues ----
        for clue_num, r, c in across_positions:
            clue_text = next((cl for cl in across_clues if cl.startswith(f"{clue_num}.")), None)
            if clue_text:
                logger.info("Solving across clue %s at (%d,%d): %s", clue_num, r, c, clue_text)

                length = count_across_length(grid_matrix, r, c)
                answer = solve_with_claude(clue_text, length)

                if is_consistent_with_grid(solution_grid, r, c, "across", answer):
                    for i, letter in enumerate(answer):
                        solution_grid[r][c + i] = letter
                else:
                    logger.warning("Inconsistent across answer for %s: %s", clue_num, answer)

        # ---- Down clues ----
        for clue_num, r, c in down_positions:
            clue_text = next((cl for cl in down_clues if cl.startswith(f"{clue_num}.")), None)
            if clue_text:
                logger.info("Solving down clue %s at (%d,%d): %s", clue_num, r, c, clue_text)

                length = count_down_length(grid_matrix, r, c)
                answer = solve_with_claude(clue_text, length)

                if is_consistent_with_grid(solution_grid, r, c, "down", answer):
                    for i, letter in enumerate(answer):
                        solution_grid[r + i][c] = letter
                else:
                    logger.warning("Inconsistent down answer for %s: %s", clue_num, answer)

        logger.info("Crossword solution grid constructed successfully")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "solution_grid": solution_grid
            })
        }

    except Exception as e:
        logger.exception("Error while solving crossword")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def solve_with_claude(clue: str, length: int, retries: int = 3) -> str:
    """
    Use Claude Sonnet 3 via Bedrock InvokeModel (body JSON).
    """
    system_prompt = (
        "You are a crossword puzzle solver. **Respond ONLY with a single English word**, "
        "no punctuation, no explanation, no surrounding text. Return the word in UPPERCASE only."
    )
    user_text = f"Crossword clue: {clue}\nProvide a single valid English word EXACTLY {length} letters long."

    for attempt in range(1, retries + 1):
        try:
            body_obj = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": length + 2,   # small allowance
                "system": system_prompt,
                "messages": [
                    {"role": "user", "content": user_text}
                ],
            }
            body_str = json.dumps(body_obj)

            # Pass body string and modelId (do NOT separately pass messages/max_tokens)
            response = bedrock.invoke_model(body=body_str, modelId=model_id)

            raw_body = response.get("body")
            if hasattr(raw_body, "read"):
                resp_text = raw_body.read().decode("utf-8")
                resp_json = json.loads(resp_text)
            elif isinstance(raw_body, str):
                resp_json = json.loads(raw_body)
            else:
                # sometimes SDK returns full parsed dict
                resp_json = response

            extracted = _extract_text_from_response(resp_json)
            logger.info("Extracted text before filter: '%s'", extracted)

            # Normalize: uppercase and keep letters only
            answer_alpha = "".join(ch for ch in (extracted or "").upper() if ch.isalpha())

            if len(answer_alpha) == length:
                logger.info("Valid answer from Claude: %s", answer_alpha)
                return answer_alpha

            logger.warning("[Attempt %d] Invalid answer length or empty: '%s' -> '%s'",
                           attempt, extracted, answer_alpha)

        except Exception as e:
            logger.error("[Attempt %d] Claude error: %s", attempt, e, exc_info=True)

    return "?" * length


def count_across_length(grid_matrix, r, c) -> int:
    """Count how many cells are available in an across slot starting at (r, c)."""
    length = 0
    cols = len(grid_matrix[0])
    while c + length < cols and grid_matrix[r][c + length] == 1:
        length += 1
    logger.info("Across length at (%d,%d): %d", r, c, length)
    return length


def count_down_length(grid_matrix, r, c) -> int:
    """Count how many cells are available in a down slot starting at (r, c)."""
    length = 0
    rows = len(grid_matrix)
    while r + length < rows and grid_matrix[r + length][c] == 1:
        length += 1
    logger.info("Down length at (%d,%d): %d", r, c, length)
    return length


def is_consistent_with_grid(solution_grid, r, c, direction, word) -> bool:
    """
    Check if a proposed word fits into the grid without conflicting with existing letters.
    """
    if direction == "across":
        for i, letter in enumerate(word):
            existing = solution_grid[r][c + i]
            if existing and existing != letter:
                logger.info("Conflict at (%d,%d): grid has %s vs %s", r, c + i, existing, letter)
                return False
    elif direction == "down":
        for i, letter in enumerate(word):
            existing = solution_grid[r + i][c]
            if existing and existing != letter:
                logger.info("Conflict at (%d,%d): grid has %s vs %s", r + i, c, existing, letter)
                return False
    return True
