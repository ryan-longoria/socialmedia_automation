import os
import boto3

def lambda_handler(event, context):
    """
    Trigger the Windows EC2 instance via SSM to upload the rendered video
    (anime_post.mp4) to the designated S3 bucket.
    """
    ssm = boto3.client('ssm')
    instance_id = os.environ.get("INSTANCE_ID")
    target_bucket = os.environ.get("TARGET_BUCKET")
    
    # Command to upload the video file from the EC2 instance to S3.
    # Adjust the local path on the EC2 instance as necessary.
    commands = [
        'aws s3 cp "C:\\path\\to\\anime_post.mp4" "s3://{}"'.format(target_bucket)
    ]
    
    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunPowerShellScript',
        Parameters={'commands': commands}
    )
    
    return {"status": "video_upload_triggered", "ssm_command": response}
