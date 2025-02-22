################################################################################
## Lambda
################################################################################

#############################
# IAM Role for Lambda Functions
#############################
resource "aws_iam_role" "lambda_role" {
  name = "anime_lambda_role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

#############################
# Lambda Functions
#############################
resource "aws_lambda_function" "fetch_rss" {
  function_name = "fetch_rss"
  filename      = "${path.module}/lambda/fetch_rss.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_role.arn
}

resource "aws_lambda_function" "process_content" {
  function_name = "process_content"
  filename      = "${path.module}/lambda/process_content.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_role.arn

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
  function_name = "store_data"
  filename      = "${path.module}/lambda/store_data.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      BUCKET_NAME = aws_s3_bucket.media_bucket.bucket
    }
  }
}

resource "aws_lambda_function" "render_video" {
  function_name = "render_video"
  filename      = "${path.module}/lambda/render_video.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      INSTANCE_ID = var.ec2_instance_id
    }
  }
}

# New Lambda to save the video to S3
resource "aws_lambda_function" "save_video" {
  function_name = "save_video"
  filename      = "${path.module}/lambda/save_video.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.8"
  role          = aws_iam_role.lambda_role.arn

  environment {
    variables = {
      INSTANCE_ID   = var.ec2_instance_id,
      TARGET_BUCKET = var.s3_bucket_name
    }
  }
}
