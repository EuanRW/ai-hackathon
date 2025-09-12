import json
import boto3

# Initialize Amazon Q client
q_client = boto3.client("qbusiness")

def lambda_handler(event, context):
    """
    AWS Lambda to solve a crossword puzzle using Amazon Q for clue solving.
    """

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

        grid_matrix = grid_data.get("grid_matrix", [])
        across_positions = grid_data.get("across_clues", [])
        down_positions = grid_data.get("down_clues", [])

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

        # ---- Across clues ----
        for clue_num, r, c in across_positions:
            clue_text = next((cl for cl in across_clues if cl.startswith(f"{clue_num}.")), None)
            if clue_text:
                length = count_across_length(grid_matrix, r, c)
                answer = solve_with_amazon_q(clue_text, length)

                if is_consistent_with_grid(solution_grid, r, c, "across", answer):
                    for i, letter in enumerate(answer):
                        solution_grid[r][c + i] = letter
                else:
                    print(f"Inconsistent across answer for {clue_num}: {answer}")
        
        # ---- Down clues ----
        for clue_num, r, c in down_positions:
            clue_text = next((cl for cl in down_clues if cl.startswith(f"{clue_num}.")), None)
            if clue_text:
                length = count_down_length(grid_matrix, r, c)
                answer = solve_with_amazon_q(clue_text, length)

                if is_consistent_with_grid(solution_grid, r, c, "down", answer):
                    for i, letter in enumerate(answer):
                        solution_grid[r + i][c] = letter
                else:
                    print(f"Inconsistent down answer for {clue_num}: {answer}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "solution_grid": solution_grid
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def solve_with_amazon_q(clue: str, length: int, retries: int = 3) -> str:
    """
    Uses Amazon Q to generate an answer for a crossword clue,
    retrying if the answer is invalid.
    """

    for attempt in range(retries):
        prompt = (
            f"Crossword clue: {clue}\n"
            f"Provide a single valid English word that is exactly {length} letters long. "
            f"Only return the word itself, no punctuation or explanation."
        )

        try:
            response = q_client.chat_sync(
                conversationId="crossword-session",
                messages=[{"role": "user", "content": [{"text": prompt}]}]
            )

            # Extract and sanitize
            answer = response["output"]["text"].strip().upper()
            answer = "".join(ch for ch in answer if ch.isalpha())

            # ---- Sanity checks ----
            if len(answer) == length and answer.isalpha():
                return answer

            print(f"[Attempt {attempt+1}] Invalid answer from Q: {answer}")

        except Exception as e:
            print(f"[Attempt {attempt+1}] Amazon Q error: {e}")

    # If all retries fail, return placeholders
    return "?" * length


def count_across_length(grid_matrix, r, c) -> int:
    """Count how many cells are available in an across slot starting at (r, c)."""
    length = 0
    cols = len(grid_matrix[0])
    while c + length < cols and grid_matrix[r][c + length] == 1:
        length += 1
    return length


def count_down_length(grid_matrix, r, c) -> int:
    """Count how many cells are available in a down slot starting at (r, c)."""
    length = 0
    rows = len(grid_matrix)
    while r + length < rows and grid_matrix[r + length][c] == 1:
        length += 1
    return length


def is_consistent_with_grid(solution_grid, r, c, direction, word) -> bool:
    """
    Check if a proposed word fits into the grid without conflicting with existing letters.
    """
    if direction == "across":
        for i, letter in enumerate(word):
            existing = solution_grid[r][c + i]
            if existing and existing != letter:
                return False
    elif direction == "down":
        for i, letter in enumerate(word):
            existing = solution_grid[r + i][c]
            if existing and existing != letter:
                return False
    return True
