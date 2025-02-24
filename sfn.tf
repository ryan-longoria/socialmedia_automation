################################################################################
## Step Functions
################################################################################

#############################
# IAM Role for Step Functions
#############################
resource "aws_iam_role" "step_functions_role" {
  name = "anime_step_functions_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "states.amazonaws.com" }
    }]
  })
}

# Policy allowing Step Functions to invoke Lambda functions
resource "aws_iam_policy" "step_functions_policy" {
  name        = "anime_step_functions_policy"
  description = "Policy for Step Functions to invoke Lambda functions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "lambda:InvokeFunction",
          "lambda:InvokeAsync"
        ],
        Resource = [
          aws_lambda_function.fetch_rss.arn,
          aws_lambda_function.process_content.arn,
          aws_lambda_function.store_data.arn,
          aws_lambda_function.render_video.arn,
          aws_lambda_function.save_video.arn,
          start_instance_arn  = aws_lambda_function.start_instance.arn,
          stop_instance_arn   = aws_lambda_function.stop_instance.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "attach_step_functions_policy" {
  role       = aws_iam_role.step_functions_role.name
  policy_arn = aws_iam_policy.step_functions_policy.arn
}

#############################
# Step Functions State Machine
#############################
resource "aws_sfn_state_machine" "anime_workflow" {
  name     = "anime_workflow"
  role_arn = aws_iam_role.step_functions_role.arn

  definition = templatefile("${path.module}/state_machine.json.tpl", {
    fetch_rss_arn       = aws_lambda_function.fetch_rss.arn,
    process_content_arn = aws_lambda_function.process_content.arn,
    store_data_arn      = aws_lambda_function.store_data.arn,
    render_video_arn    = aws_lambda_function.render_video.arn,
    save_video_arn      = aws_lambda_function.save_video.arn
  })
}

#############################
# CloudWatch Event Rule to Trigger the State Machine
#############################
resource "aws_cloudwatch_event_rule" "workflow_schedule" {
  name                = "anime_workflow_schedule"
  schedule_expression = "rate(5 minutes)"
}

resource "aws_iam_role" "eventbridge_role" {
  name = "eventbridge_step_functions_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action    = "sts:AssumeRole",
      Effect    = "Allow",
      Principal = { Service = "events.amazonaws.com" }
    }]
  })
}

resource "aws_iam_policy" "eventbridge_policy" {
  name        = "eventbridge_step_functions_policy"
  description = "Policy for CloudWatch Event to start Step Functions executions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = "states:StartExecution",
      Resource = aws_sfn_state_machine.anime_workflow.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "attach_eventbridge_policy" {
  role       = aws_iam_role.eventbridge_role.name
  policy_arn = aws_iam_policy.eventbridge_policy.arn
}

resource "aws_cloudwatch_event_target" "state_machine_target" {
  rule      = aws_cloudwatch_event_rule.workflow_schedule.name
  target_id = "StepFunctionStateMachine"
  arn       = aws_sfn_state_machine.anime_workflow.arn
  role_arn  = aws_iam_role.eventbridge_role.arn
}