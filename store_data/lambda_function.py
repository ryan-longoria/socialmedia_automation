import json
import boto3

s3 = boto3.client('s3')
BUCKET_NAME = "your-s3-bucket"


def lambda_handler(event, context):
    """Store the processed post data in S3 as a JSON file.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary indicating storage status and S3 key used.
    """
    post = event.get("post", {})
    json_data = json.dumps(post, indent=4)
    s3.put_object(Bucket=BUCKET_NAME, Key="most_recent_post.json", Body=json_data)
    return {"status": "stored", "s3_key": "most_recent_post.json"}
