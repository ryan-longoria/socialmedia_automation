################################################################################
## Step Functions
################################################################################

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
    save_video_arn      = aws_lambda_function.save_video.arn,
    start_instance_arn  = aws_lambda_function.start_instance.arn,
    stop_instance_arn   = aws_lambda_function.stop_instance.arn,
    notify_post_arn     = aws_lambda_function.notify_post.arn
  })
}
