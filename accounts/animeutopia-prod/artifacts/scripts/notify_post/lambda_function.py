import os
import logging
import boto3
import uuid
import json
import requests
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    bucket = os.environ.get("TARGET_BUCKET")
    if not bucket:
        error_msg = "TARGET_BUCKET environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    teams_webhook_url = os.environ.get("TEAMS_WEBHOOK_URL")
    if not teams_webhook_url:
        error_msg = "TEAMS_WEBHOOK_URL environment variable not set."
        logger.error(error_msg)
        return {"error": error_msg}

    s3 = boto3.client("s3")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique_id = uuid.uuid4().hex

    video_key = event.get("videoResult", {}).get("video_s3_key", f"anime_post_{timestamp}_{unique_id}.mp4")
    project_key = event.get("project_key", f"exports/anime_template_exported_{timestamp}_{unique_id}.aep")

    try:
        video_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": video_key},
            ExpiresIn=604800
        )
    except Exception as e:
        logger.exception("Error generating presigned URL for video file: %s", e)
        return {"error": "Failed to generate presigned URL for video file."}

    try:
        project_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": project_key},
            ExpiresIn=604800
        )
    except Exception as e:
        logger.exception("Error generating presigned URL for project file: %s", e)
        return {"error": "Failed to generate presigned URL for project file."}

    message_text = (
        f"Your new post has been processed!\n\n"
        f"**Video URL**: {video_url}\n\n"
        f"**After Effects Project URL**: {project_url}"
    )

    teams_payload = {
        "text": message_text
    }

    try:
        response = requests.post(
            teams_webhook_url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(teams_payload)
        )
        response.raise_for_status()
    except Exception as e:
        logger.exception("Error posting message to Microsoft Teams: %s", e)
        return {"error": "Failed to post to Microsoft Teams channel."}

    logger.info("Message posted to Microsoft Teams successfully.")
    return {
        "status": "message_posted",
        "video_url": video_url,
        "project_url": project_url,
        "video_key": video_key,
        "project_key": project_key
    }
