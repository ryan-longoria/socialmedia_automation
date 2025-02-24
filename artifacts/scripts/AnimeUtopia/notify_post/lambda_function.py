import boto3
import os
import json

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    bucket = os.environ.get("TARGET_BUCKET")
    
    # Generate pre-signed URL for video file (assumed key is "anime_post.mp4")
    video_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': "anime_post.mp4"},
        ExpiresIn=3600
    )
    
    # Invoke the upload_project Lambda to get the project URL.
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=os.environ.get("UPLOAD_PROJECT_LAMBDA"),
        InvocationType='RequestResponse'
    )
    
    payload = json.loads(response['Payload'].read())
    project_url = payload.get("project_url", "No project URL")
    
    # Compose the email message with both links.
    subject = "New Anime Post & Project Export are Ready!"
    message = (
        f"Your new post has been processed.\n"
        f"Video: {video_url}\n"
        f"After Effects Project: {project_url}\n"
    )
    
    # Publish to SNS.
    sns = boto3.client('sns')
    topic_arn = os.environ.get("SNS_TOPIC_ARN")
    sns.publish(
        TopicArn=topic_arn,
        Subject=subject,
        Message=message
    )
    
    return {
        "status": "notification_sent",
        "video_url": video_url,
        "project_url": project_url
    }