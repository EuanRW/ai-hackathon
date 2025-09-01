terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# === Variables ===
variable "default_tags" {
  type = map(string)
  default = {
    Project     = "ai-hackathon"
    Environment = "dev"
    Owner       = "team8"
    Terraform   = "true"
  }
}

provider "aws" {
  region = "eu-west-2"

  default_tags {
    tags = var.default_tags
  }
}

# S3 bucket for crossword_images
resource "aws_s3_bucket" "crossword_images" {
  bucket = "ai-hackathon-crossword-images"
}

# S3 bucket for Lambda layers
resource "aws_s3_bucket" "lambda_layer_bucket" {
  bucket = "ai-hackathon-lambda-layers"
}

# Upload OpenCV + NumPy layer zip to S3
resource "aws_s3_object" "opencv_numpy_zip" {
  bucket = aws_s3_bucket.lambda_layer_bucket.id
  key    = "opencv-numpy.zip"
  source = "${path.module}/opencv-numpy.zip"
}

# Lambda Layer: OpenCV + NumPy
resource "aws_lambda_layer_version" "opencv_numpy" {
  s3_bucket = aws_s3_object.opencv_numpy_zip.bucket
  s3_key    = aws_s3_object.opencv_numpy_zip.key
  layer_name = "opencv-numpy"
  compatible_runtimes = ["python3.9", "python3.11"]
  description = "Lambda layer with OpenCV and NumPy"
}

# Lambda IAM Role
resource "aws_iam_role" "lambda_exec" {
  name = "lambda-exec-role"

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

# IAM policy to allow Lambda to read objects from S3 bucket 
resource "aws_iam_policy" "lambda_s3_read" {
  name        = "lambda-s3-read-policy"
  description = "Allow Lambda to read images from S3 bucket"

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

# IAM policy attachment for S3 read
resource "aws_iam_role_policy_attachment" "lambda_s3_read_attach" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.lambda_s3_read.arn
}


# IAM policy attachment for logs
resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda Function
resource "aws_lambda_function" "grid_detection_function" {
  function_name = "grid-detection-function"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.11"
  role          = aws_iam_role.lambda_exec.arn
  filename      = "${path.module}/grid-detect-function.zip"

  layers = [
    aws_lambda_layer_version.opencv_numpy.arn
  ]

  memory_size = 1024
  timeout     = 30

  source_code_hash = filebase64sha256("${path.module}/grid-detect-function.zip")  # triggers updates

  tags = {
    Component = "Lambda Function"
  }
}

