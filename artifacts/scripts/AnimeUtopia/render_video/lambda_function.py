import boto3
import json
import os

def lambda_handler(event, context):
    """Trigger the video rendering process on a Windows EC2 instance using SSM.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary indicating the status of the video render trigger.
    """
    post = event.get("post", {})
    ssm = boto3.client('ssm')
    instance_id = os.environ.get("INSTANCE_ID")

    response = ssm.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': [
            'afterfx.exe -r automate_aftereffects.jsx'
        ]}
    )
    return {"status": "video_render_triggered", "ssm_command": response}
