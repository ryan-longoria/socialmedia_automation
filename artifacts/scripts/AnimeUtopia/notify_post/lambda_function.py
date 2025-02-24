import boto3
import os

def lambda_handler(event, context):
    """
    Combines the process of generating a pre-signed URL for a rendered video and
    uploading the exported After Effects project file to S3, then generating its
    pre-signed URL. It sends both links in an SNS notification email.

    This function performs the following:
    1. Generates a pre-signed URL for the video file ("anime_post.mp4").
    2. Uploads the exported After Effects project file ("anime_template_exported.aep") 
       to S3 under the "exports/" prefix.
    3. Generates a pre-signed URL for the uploaded project file.
    4. Publishes an SNS notification containing both URLs.

    Environment Variables:
      - TARGET_BUCKET: Name of the S3 bucket where files are stored.
      - SNS_TOPIC_ARN: ARN of the SNS topic for notifications.

    Args:
        event (dict): Event data passed by the caller (unused in this function).
        context (object): Lambda context object (unused).

    Returns:
        dict: A dictionary containing the status, video_url, and project_url.
    """
    s3 = boto3.client('s3')
    bucket = os.environ.get("TARGET_BUCKET")
    
    video_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': "anime_post.mp4"},
        ExpiresIn=3600
    )
    
    local_project_file = "anime_template_exported.aep" 
    s3_project_key = "exports/" + local_project_file
    try:
        s3.upload_file(local_project_file, bucket, s3_project_key)
    except Exception as upload_error:
        return {"error": f"Failed to upload project file: {upload_error}"}
    
    project_url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': bucket, 'Key': s3_project_key},
        ExpiresIn=3600
    )
    
    subject = "New AnimeUtopia Post is Ready!"
    message = (
        f"Your new post has been processed.\n\n"
        f"Video URL: {video_url}\n\n"
        f"After Effects Project URL: {project_url}"
    )
    
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