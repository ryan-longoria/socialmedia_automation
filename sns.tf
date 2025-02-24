resource "aws_sns_topic" "anime_notifications" {
  name = "anime_post_notifications"
}

resource "aws_sns_topic_subscription" "animeutopia_subscription" {
  topic_arn = aws_sns_topic.animeutopia_notifications.arn
  protocol  = "email"
  endpoint  = "kk47mgmt@outlook.com"
}