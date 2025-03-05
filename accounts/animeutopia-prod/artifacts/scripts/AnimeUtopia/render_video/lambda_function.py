import os
import json
import logging
import boto3
import time
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def default_serializer(o):
    """
    Serialize datetime objects as ISO formatted strings.
    """
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")

def wait_for_ssm_registration(ssm_client, instance_id, timeout=300, interval=10):
    """
    Wait until the given instance is registered with SSM.
    """
    waited = 0
    while waited < timeout:
        info = ssm_client.describe_instance_information()
        registered_ids = [
            i["InstanceId"]
            for i in info.get("InstanceInformationList", [])
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
    Trigger the video rendering process on a Windows EC2 instance using SSM.
    
    This function:
      1. Ensures the EC2 instance is running.
      2. Waits until the instance registers with SSM.
      3. Generates a presigned URL for the JSON file stored in S3.
      4. Updates the C:\\animeutopia\\automate_aftereffects.jsx file by replacing the
         placeholder line for the presigned URL with the actual generated URL.
      5. Runs After Effects (using the full path) on the EC2 instance with the updated script.

    Environment Variables:
      - INSTANCE_ID: The EC2 instance ID.
      - TARGET_BUCKET: The S3 bucket name where the JSON file is stored.
    """

    instance_id = os.environ.get("INSTANCE_ID")
    if not instance_id:
        error_msg = "INSTANCE_ID environment variable not set."
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

    try:
        s3 = boto3.client("s3")
        bucket_name = os.environ.get("TARGET_BUCKET")
        if not bucket_name or not isinstance(bucket_name, str):
            error_msg = "TARGET_BUCKET environment variable not set or invalid."
            logger.error(error_msg)
            return {"error": error_msg}

        key = "most_recent_post.json"
        presigned_url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=3600
        )
        logger.info("Generated presigned URL: %s", presigned_url)
        logger.info("Type of presigned_url: %s", type(presigned_url))

    except Exception as e:
        logger.exception("Failed to generate presigned URL: %s", e)
        return {"error": f"Failed to generate presigned URL: {e}"}

    afterfx_full_path = r"C:\Program Files\Adobe\Adobe After Effects 2025\Support Files\afterfx.exe"

    try:
        ps_command = (
            '(Get-Content "C:\\animeutopia\\automate_aftereffects.jsx" -Raw) '
            '-replace \'var s3JsonUrl = "{{PRESIGNED_URL}}";\', \'var s3JsonUrl = "{}";\' '
            '| Set-Content "C:\\animeutopia\\automate_aftereffects.jsx"; '
            '"{}" -r "C:\\animeutopia\\automate_aftereffects.jsx"'
        ).format(
            presigned_url,
            afterfx_full_path
        )
        logger.info("PowerShell command: %s", ps_command)
    except Exception as e:
        logger.exception("Failed to build PowerShell command: %s", e)
        return {"error": f"Failed to build PowerShell command: {e}"}

    try:
        ssm_response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={"commands": [ps_command]},
        )
        logger.info("SSM command sent successfully: %s", ssm_response)
        response_dict = {
            "status": "video_render_triggered",
            "ssm_command": ssm_response,
        }
        serialized = json.dumps(response_dict, default=default_serializer)
        return json.loads(serialized)
    except Exception as e:
        logger.exception("Failed to send SSM command: %s", e)
        return {"error": f"Failed to send SSM command: {e}"}
