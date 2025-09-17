# IAM Role for Lambda
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

# IAM Policy - Allow Lambda to call Amazon Bedrock
resource "aws_iam_policy" "crossword_solver_bedrock_policy" {
  name        = "crossword-solver-bedrock-policy"
  description = "Allow Lambda to call Amazon Bedrock APIs (Claude 4)"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"  # You can restrict to specific model ARNs later
      }
    ]
  })
}

# Attach policies
resource "aws_iam_role_policy_attachment" "crossword_solver_bedrock_attach" {
  role       = aws_iam_role.crossword_solver_exec.name
  policy_arn = aws_iam_policy.crossword_solver_bedrock_policy.arn
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

  environment {
    variables = {
      BEDROCK_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
    }
  }



  tags = {
    Component = "Crossword Solver Lambda"
  }
}

output "crossword_solver_lambda_name" {
  value       = aws_lambda_function.crossword_solver_function.function_name
  description = "Lambda function for crossword solver using Claude 4 on Bedrock"
}