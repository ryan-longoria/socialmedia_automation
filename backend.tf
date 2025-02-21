################################################################################
## Empty Backend Declaration - Configured by `--backend-config=backends/...`
################################################################################

terraform {
  backend "s3" {
    bucket = var.terraform_backend_bucket
    key    = "tfstate/${local.project}/terraform.tfstate"
    region = var.aws_region
  }
}