import os
import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    """
    Trigger the video rendering process on a Windows EC2 instance using SSM.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary indicating the status of the video render trigger.
    """
    post = event.get("post", {})
    instance_id = os.environ.get("INSTANCE_ID")
    if not instance_id:
        error_msg = "INSTANCE_ID environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    ssm = boto3.client("ssm")
    try:
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunShellScript",
            Parameters={
                "commands": [
                    "afterfx.exe -r automate_aftereffects.jsx"
                ]
            }
        )
        logger.info("SSM command sent successfully: %s", response)
        return {"status": "video_render_triggered", "ssm_command": response}
    except Exception as e:
        logger.exception("Failed to send SSM command: %s", e)
        return {"error": f"Failed to send SSM command: {e}"}
