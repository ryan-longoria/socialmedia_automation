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

    Args:
        o: Object to serialize.

    Raises:
        TypeError: If object type is not serializable.

    Returns:
        str: ISO formatted datetime string.
    """
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")


def wait_for_ssm_registration(ssm_client, instance_id, timeout=300, interval=10):
    """
    Wait until the given instance is registered with SSM.

    Args:
        ssm_client: Boto3 SSM client.
        instance_id (str): The EC2 instance ID.
        timeout (int): Total time to wait in seconds.
        interval (int): Interval between checks in seconds.

    Returns:
        bool: True if the instance is registered within the timeout, False otherwise.
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
      4. Reads a JSX template file (with a {{PRESIGNED_URL}} placeholder),
         replaces the placeholder with the generated URL, and writes the
         updated script to a target file.
      5. Sends an SSM command to run After Effects with the updated script.

    Environment Variables:
      - INSTANCE_ID: The EC2 instance ID.
      - TARGET_BUCKET: The S3 bucket name where the JSON file is stored.

    Args:
        event (dict): Lambda event data.
        context (object): Lambda context object.

    Returns:
        dict: A dictionary indicating the status of the command.
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
            logger.info("Instance %s is in state '%s'. Waiting...", instance_id,
                        instance_state)
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
        key = "most_recent_post.json"
        presigned_url = s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket_name, "Key": key},
            ExpiresIn=3600  
        )
        logger.info("Generated presigned URL: %s", presigned_url)

        jsx_template_path = r"C:\animeutopia\automate_aftereffects_template.jsx"
        jsx_script_path = r"C:\animeutopia\automate_aftereffects.jsx"

        with open(jsx_template_path, "r") as f:
            jsx_template = f.read()
        updated_jsx = jsx_template.replace("{{PRESIGNED_URL}}", presigned_url)
        with open(jsx_script_path, "w") as f:
            f.write(updated_jsx)
        logger.info("After Effects script updated with presigned URL.")
    except Exception as e:
        logger.exception("Failed to update JSX script: %s", e)
        return {"error": f"Failed to update JSX script: {e}"}
