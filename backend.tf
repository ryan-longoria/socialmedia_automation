################################################################################
## Empty Backend Declaration - Configured by `--backend-config=backends/...`
################################################################################

terraform {
  backend "s3" {
    bucket = "my-terraform-backend-bucket-unique"
    key    = "tfstate/animeutopia/terraform.tfstate"
    region = "us-east-2"
  }
}