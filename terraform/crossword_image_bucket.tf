# S3 bucket for crossword_images
resource "aws_s3_bucket" "crossword_images" {
  bucket = "ai-hackathon-crossword-images"
}