import boto3
import json


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
    response = ssm.send_command(
        InstanceIds=['i-your-ec2-instance-id'],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': [
            'cd C:\\path\\to\\your\\aftereffects\\scripts',
            f'node render_script.js \'{json.dumps(post)}\''
        ]}
    )
    return {"status": "video_render_triggered", "ssm_command": response}
