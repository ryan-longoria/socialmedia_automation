################################################################################
## Providers Declared Here - Configured by variables
################################################################################

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
        DeployedBy = "Terraform"
    }
  }
}
