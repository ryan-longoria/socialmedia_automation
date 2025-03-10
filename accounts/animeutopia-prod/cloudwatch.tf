################################################################################
## Cloudwatch
################################################################################

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