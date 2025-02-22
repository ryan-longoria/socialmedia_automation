################################################################################
## Empty Backend Declaration - Configured by `--backend-config=backends/...`
################################################################################

terraform {
  backend "s3" {
    bucket = "nonprod-animeutopia-backend-bucket"
    key    = "tfstate/animeutopia/terraform.tfstate"
    region = "us-east-2"
  }
}