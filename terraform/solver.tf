# IAM Role for Crossword Solver Lambda
resource "aws_iam_role" "crossword_solver_exec" {
  name = "crossword-solver-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy - Allow Lambda to call Amazon Q
resource "aws_iam_policy" "crossword_solver_q_policy" {
  name        = "crossword-solver-q-policy"
  description = "Allow Lambda to call Amazon Q chat APIs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "qbusiness:ChatSync",
          "qbusiness:ChatAsync"
        ]
        Resource = "*" # tighten later to specific Q application ARN
      }
    ]
  })
}

# Attach Policies
resource "aws_iam_role_policy_attachment" "crossword_solver_q_attach" {
  role       = aws_iam_role.crossword_solver_exec.name
  policy_arn = aws_iam_policy.crossword_solver_q_policy.arn
}

resource "aws_iam_role_policy_attachment" "crossword_solver_logging" {
  role       = aws_iam_role.crossword_solver_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function
resource "aws_lambda_function" "crossword_solver_function" {
  function_name = "crossword-solver-function"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.crossword_solver_exec.arn
  filename      = "${path.module}/utils/solver-function.zip"

  memory_size      = 1024
  timeout          = 60
  source_code_hash = filebase64sha256("${path.module}/utils/solver-function.zip")

  tags = {
    Component = "Crossword Solver Lambda"
  }
}
