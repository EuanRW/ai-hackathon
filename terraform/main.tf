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


