import os
import json
import uuid
import boto3
import requests
from moviepy.editor import ImageClip, TextClip, CompositeVideoClip

s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket_name = os.environ.get("TARGET_BUCKET", "my-bucket")
    json_key = "most_recent_post.json"
    output_key = f"outputs/anime_post_{uuid.uuid4().hex}.mp4"

    local_json = "/tmp/most_recent_post.json"
    s3.download_file(bucket_name, json_key, local_json)

    with open(local_json, "r", encoding="utf-8") as f:
        post_data = json.load(f)

    title_text = post_data.get("title", "No Title")
    description_text = post_data.get("description", "")
    image_path = post_data.get("image_path", None)

    bg_local_path = "/tmp/background.jpg"
    if image_path and image_path.startswith("http"):
        try:
            resp = requests.get(image_path, timeout=10)
            with open(bg_local_path, "wb") as f:
                f.write(resp.content)
        except Exception as e:
            print("Image download failed:", e)
            bg_local_path = None
    elif image_path:
        try:
            s3.download_file(bucket_name, image_path, bg_local_path)
        except Exception as e:
            print("Failed to download image from S3:", e)
            bg_local_path = None

    width, height = 1280, 720
    duration_sec = 10

    if bg_local_path and os.path.exists(bg_local_path):
        bg_clip = ImageClip(bg_local_path).resize((width, height)).set_duration(duration_sec)
    else:
        from moviepy.editor import ColorClip
        bg_clip = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration_sec)

    title_clip = TextClip(txt=title_text, fontsize=60, color='white',
                          size=(width, None), method='caption').set_duration(duration_sec).set_position(("center", "top"))
    desc_clip = TextClip(txt=description_text, fontsize=40, color='yellow',
                         size=(width, None), method='caption').set_duration(duration_sec).set_position(("center", "center"))

    final_clip = CompositeVideoClip([bg_clip, title_clip, desc_clip], size=(width, height))
    final_clip = final_clip.set_duration(duration_sec)

    local_mp4 = "/tmp/anime_post.mp4"
    final_clip.write_videofile(local_mp4, fps=24, codec="libx264", audio=False)

    s3.upload_file(local_mp4, bucket_name, output_key)

    return {
        "status": "rendered",
        "video_s3_key": output_key
    }
