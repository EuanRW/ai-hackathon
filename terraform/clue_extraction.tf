# IAM Role for Clue Extraction Lambda
resource "aws_iam_role" "clue_extraction_exec" {
  name = "clue-extraction-lambda-exec"

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

# IAM Policies

# Allow Lambda to read crossword images
resource "aws_iam_policy" "clue_extraction_s3_read" {
  name        = "clue-extraction-s3-read-policy"
  description = "Allow Lambda to read crossword images from S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = "${aws_s3_bucket.crossword_images.arn}/*"
      }
    ]
  })
}

# Allow Lambda to use Textract
resource "aws_iam_policy" "clue_extraction_textract" {
  name        = "clue-extraction-textract-policy"
  description = "Allow Lambda to call Textract APIs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "textract:AnalyzeDocument",
          "textract:DetectDocumentText",
          "textract:GetDocumentAnalysis"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach Policies
resource "aws_iam_role_policy_attachment" "clue_extraction_s3_read_attach" {
  role       = aws_iam_role.clue_extraction_exec.name
  policy_arn = aws_iam_policy.clue_extraction_s3_read.arn
}

resource "aws_iam_role_policy_attachment" "clue_extraction_textract_attach" {
  role       = aws_iam_role.clue_extraction_exec.name
  policy_arn = aws_iam_policy.clue_extraction_textract.arn
}

resource "aws_iam_role_policy_attachment" "clue_extraction_logging" {
  role       = aws_iam_role.clue_extraction_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function
resource "aws_lambda_function" "clue_extraction_function" {
  function_name = "clue-extraction-function"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.clue_extraction_exec.arn
  filename      = "${path.module}/utils/clue-extraction-function.zip"

  memory_size      = 1024
  timeout          = 30
  source_code_hash = filebase64sha256("${path.module}/utils/clue-extraction-function.zip")

  tags = {
    Component = "Clue Extraction Lambda"
  }
}
