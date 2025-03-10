################################################################################
## Lambda
################################################################################

resource "aws_lambda_function" "fetch_rss" {
  function_name      = "fetch_rss"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/fetch_rss/fetch_rss.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/fetch_rss/fetch_rss.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10
}

resource "aws_lambda_function" "process_content" {
  function_name      = "process_content"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/process_content/process_content.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/process_content/process_content.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      IMAGE_MAGICK_EXE = "/opt/bin/magick"
    }
  }

  layers = [
    "arn:aws:lambda:us-east-2:481665084477:layer:imagick-layer:1"
  ]
}

resource "aws_lambda_function" "store_data" {
  function_name      = "store_data"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/store_data/store_data.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/store_data/store_data.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.media_bucket.bucket
    }
  }
}

resource "aws_lambda_function" "render_video" {
  function_name      = "render_video"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/render_video/render_video.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/render_video/render_video.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 180

  environment {
    variables = {
      INSTANCE_ID   = var.ec2_instance_id
      TARGET_BUCKET = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "save_video" {
  function_name      = "save_video"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/save_video/save_video.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/save_video/save_video.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 180

  environment {
    variables = {
      INSTANCE_ID   = var.ec2_instance_id,
      TARGET_BUCKET = var.s3_bucket_name
    }
  }
}

resource "aws_lambda_function" "start_instance" {
  function_name      = "start_instance"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/start_instance/start_instance.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/start_instance/start_instance.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      EC2_INSTANCE_ID = var.ec2_instance_id
    }
  }
}

resource "aws_lambda_function" "stop_instance" {
  function_name      = "stop_instance"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/stop_instance/stop_instance.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/stop_instance/stop_instance.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      EC2_INSTANCE_ID = var.ec2_instance_id
    }
  }
}

resource "aws_lambda_function" "notify_post" {
  function_name      = "notify_post"
  filename           = "${path.module}/artifacts/scripts/AnimeUtopia/notify_post/notify_post.zip"
  source_code_hash   = filebase64sha256("${path.module}/artifacts/scripts/AnimeUtopia/notify_post/notify_post.zip")
  handler            = "lambda_function.lambda_handler"
  runtime            = "python3.9"
  role               = aws_iam_role.lambda_role.arn
  timeout            = 10

  environment {
    variables = {
      TEAMS_WEBHOOK_URL = var.teams_webhook_url,
      TARGET_BUCKET = var.s3_bucket_name
    }
  }
}
