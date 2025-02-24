import boto3
import os

def lambda_handler(event, context):
    bucket = os.environ.get("TARGET_BUCKET")
    video_key = "anime_post.mp4"
    s3 = boto3.client('s3')
    video_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': video_key},
        ExpiresIn=3600
    )

    subject = "New AnimeUtopia Post is Ready!"
    message = f"Your new post has been processed. Access the mp4 here: {video_url}"

    sns = boto3.client('sns')
    topic_arn = os.environ.get("SNS_TOPIC_ARN")
    response = sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message
    )

    return {
        "status": "notification_sent",
        "sns_response": response,
        "video_url": video_url
    }
