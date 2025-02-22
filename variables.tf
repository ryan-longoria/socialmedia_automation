################################################################################
## Terraform Variables
################################################################################

variable "aws_account_id" {
  description = "The AWS Account ID. Used for configuring the provider and defining ECS resources."
  type = string
}

variable "aws_region" {
  description = "The AWS region to deploy resources."
  type        = string
  default     = "us-east-2"
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket to store media assets."
  type        = string
  default     = "my-anime-media-bucket-unique"
}

variable "environment" {
  description = "The environment name (e.g., dev, prod)."
  type        = string
  default     = "dev"
}

variable "ec2_instance_id" {
  description = "The ID of the Windows EC2 instance with Photoshop installed."
  type        = string
  default     = "i-022e9bb5447996955"
}

variable "terraform_backend_bucket" {
  description = "The S3 bucket used to store Terraform state."
  type        = string
  default     = "animeutopia-bucket"
}
