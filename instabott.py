from instagrapi import Client
import os
from moviepy.editor import VideoFileClip
from PIL import Image

video_path = "anime_post.mp4"
if not os.path.exists(video_path):
    raise FileNotFoundError(f"The video file '{video_path}' does not exist.")

clip = VideoFileClip(video_path)
width, height = clip.size
new_height = 1920
new_width = int(new_height * width / height)
clip_resized = clip.resize(newsize=(new_width, new_height))

resized_video_path = "resized_anime_post.mp4"
clip_resized.write_videofile(resized_video_path, codec="libx264")

client = Client()

client.login(username="secret-placeholder", password="secret-placeholder")

try:
    client.clip_upload(
        resized_video_path,
        caption="Check out the latest anime news! 🎥✨ #anime #animeutopianews",
        configure_timeout=15
    )
    print("Reel uploaded successfully!")
except Exception as e:
    print(f"Error uploading Reel: {e}"

os.remove(resized_video_path)
