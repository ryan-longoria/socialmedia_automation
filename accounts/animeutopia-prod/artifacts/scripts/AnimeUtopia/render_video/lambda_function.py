import os
import json
import logging
import boto3
import time
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def default_serializer(o):
    if isinstance(o, datetime):
        return o.isoformat()
    raise TypeError(f"Type {type(o)} not serializable")

def wait_for_ssm_registration(ssm_client, instance_id, timeout=300, interval=10):
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
    instance_id = os.environ.get("INSTANCE_ID")
    if not instance_id:
        error_msg = "INSTANCE_ID env var not set."
        logger.error(error_msg)
        return {"error": error_msg}
    
    ec2 = boto3.client("ec2")
    waited = 0
    while waited < 300:
        resp = ec2.describe_instances(InstanceIds=[instance_id])
        state = resp["Reservations"][0]["Instances"][0]["State"]["Name"]
        if state == "running":
            logger.info("Instance %s is running.", instance_id)
            break
        else:
            logger.info("Instance %s state is '%s'. Waiting...", instance_id, state)
            time.sleep(10)
            waited += 10
    else:
        error_msg = f"Instance {instance_id} not 'running' after 300s."
        logger.error(error_msg)
        return {"error": error_msg}
    
    ssm = boto3.client("ssm")
    if not wait_for_ssm_registration(ssm, instance_id):
        error_msg = f"Instance {instance_id} not registered with SSM after timeout."
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
    except Exception as e:
        logger.exception("Failed to generate presigned URL.")
        return {"error": str(e)}
    
    ps_command = f'''
    Write-Host "Checking aerender version..."
    & aerender.exe -version

    Write-Host "Setting environment variable for most_recent_post.json..."
    $Env:PRESIGNED_URL = "{presigned_url}"

    Write-Host "Starting After Effects render..."
    & aerender.exe -project "C:\\animeutopia\\anime_template.aep" `
                -comp "standard-news-template" `
                -output "C:\\animeutopia\\output\\anime_post.mp4"
    '''

    
    try:
        ssm_response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName="AWS-RunPowerShellScript",
            Parameters={"commands": [ps_command]},
        )
        logger.info("SSM command sent: %s", ssm_response)
        
        return json.loads(json.dumps(
            {"status": "render_triggered", "ssm_command": ssm_response},
            default=default_serializer
        ))
    except Exception as e:
        logger.exception("Failed to send SSM command.")
        return {"error": str(e)}
