################################################################################
## Module Calls and Resources
################################################################################

#############################
# S3 Bucket for Assets
#############################
resource "aws_s3_bucket" "media_bucket" {
  bucket = var.s3_bucket_name
  acl    = "private"

  versioning {
    enabled = true
  }

  tags = {
    Name        = "AnimeMediaBucket"
    Environment = var.environment
  }
}
