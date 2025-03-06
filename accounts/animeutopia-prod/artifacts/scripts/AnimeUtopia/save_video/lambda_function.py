import os
import logging
import boto3
import time
import json
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def default_serializer(o):
    """
    Serialize datetime objects to ISO 8601 strings.
    """
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")


def wait_for_ssm_registration(ssm_client, instance_id, timeout=300, interval=10):
    """
    Wait until the EC2 instance is registered with SSM.
    
    Args:
        ssm_client: A boto3 SSM client.
        instance_id: The EC2 instance ID.
        timeout: Maximum wait time in seconds.
        interval: Time in seconds between checks.
        
    Returns:
        True if the instance is registered, False otherwise.
    """
    waited = 0
    while waited < timeout:
        info = ssm_client.describe_instance_information()
        registered_ids = [
            i["InstanceId"] for i in info.get("InstanceInformationList", [])
            if i.get("PingStatus") == "Online"
        ]
        if instance_id in registered_ids:
            logger.info("Instance %s is registered with SSM.", instance_id)
            return True
        else:
            logger.info("Instance %s not yet registered with SSM. Waiting...", instance_id)
            time.sleep(interval)
            waited += interval
    return False


def lambda_handler(event, context):
    """
    Trigger the Windows EC2 instance via SSM to upload the rendered video
    (anime_post.mp4) and the After Effects project file (anime_template_exported.aep)
    to the designated S3 bucket. These files are expected to be located in the EC2
    instance's default working directory (typically the home directory of the user
    running the SSM command). If your files are stored elsewhere, you must use full paths.
    
    Environment Variables:
      - INSTANCE_ID: The EC2 instance ID.
      - TARGET_BUCKET: The S3 bucket where files should be uploaded.
    
    Returns:
        dict: Status message and SSM command details.
    """
    instance_id = os.environ.get("INSTANCE_ID")
    target_bucket = os.environ.get("TARGET_BUCKET")

    if not instance_id:
        error_msg = "INSTANCE_ID environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    if not target_bucket:
        error_msg = "TARGET_BUCKET environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    ec2 = boto3.client("ec2")
    waited = 0
    while waited < 300:
        response = ec2.describe_instances(InstanceIds=[instance_id])
        instance_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]
        if instance_state == "running":
            logger.info("Instance %s is running.", instance_id)
            break
        else:
            logger.info("Instance %s is in state '%s'. Waiting...", instance_id, instance_state)
            time.sleep(10)
            waited += 10
    else:
        error_msg = f"Instance {instance_id} did not become running within timeout."
        logger.error(error_msg)
        return {"error": error_msg}

    ssm = boto3.client("ssm")
    if not wait_for_ssm_registration(ssm, instance_id):
        error_msg = f"Instance {instance_id} did not register with SSM within timeout."
        logger.error(error_msg)
        return {"error": error_msg}

    commands = [
        f'cd "C:\\animeutopia\\output"; aws s3 cp "anime_post.mp4" "s3://{target_bucket}/anime_post.mp4"',
        f'cd "C:\\animeutopia\\output"; aws s3 cp "anime_template_exported.aep" "s3://{target_bucket}/exports/anime_template_exported.aep"'
    ]

    try:
        ssm_response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={"commands": commands}
        )
        logger.info("SSM command sent successfully: %s", ssm_response)
        response_dict = {
            "status": "video_upload_triggered",
            "ssm_command": ssm_response
        }
        serialized = json.dumps(response_dict, default=default_serializer)
        return json.loads(serialized)
    except Exception as e:
        logger.exception("Failed to send SSM command: %s", e)
        return {"error": f"Failed to send SSM command: {e}"}
