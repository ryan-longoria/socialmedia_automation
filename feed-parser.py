import feedparser
import requests
from fuzzywuzzy import fuzz, process
import spacy
import os
import json
import re
from urllib.parse import urlparse
import subprocess
from PIL import Image

ANILIST_API_URL = "https://graphql.anilist.co"
OUTPUT_JSON_FILE = "most_recent_post.json"

nlp = spacy.load("en_core_web_sm")

# Set the full path to the ImageMagick executable on your system.
IMAGE_MAGICK_EXE = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

def fetch_anilist_titles_and_image(core_title):
    query = """
    query ($searchTitle: String) {
      Media(type: ANIME, search: $searchTitle) {
        title {
          romaji
          english
          native
        }
        coverImage {
          extraLarge
          large
          medium
        }
      }
    }
    """
    variables = {'searchTitle': core_title}

    print("Sending request to AniList API with payload:")
    print(json.dumps({"query": query, "variables": variables}, indent=4))

    try:
        response = requests.post(ANILIST_API_URL, json={"query": query, "variables": variables})
        response.raise_for_status()
        data = response.json()

        print("AniList API response:")
        print(json.dumps(data, indent=4))

        titles = []
        image_url = None
        if "Media" in data["data"]:
            media = data["data"]["Media"]
            titles.extend(filter(None, [media["title"]["romaji"], media["title"]["english"], media["title"]["native"]]))
            image_url = media["coverImage"]["extraLarge"]
        
        # Download and convert the image if URL is found
        if image_url:
            image_path = download_image(image_url)
        else:
            image_path = None

        return titles, image_path
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    return [], None

def download_image(url):
    file_path = os.path.join(os.getcwd(), "backgroundimage.jpg")
    try:
        print(f"Downloading image from: {url}")
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Image saved to: {file_path}")
        
        # Check file size (if too small, likely incomplete)
        file_size = os.path.getsize(file_path)
        print(f"Downloaded file size: {file_size} bytes")
        if file_size < 1000:
            print("Error: File size too small, likely incomplete.")
            return None
        
        # Use ImageMagick to convert the file to a proper JPEG
        converted_path = os.path.join(os.getcwd(), "backgroundimage_converted.jpg")
        try:
            subprocess.run([IMAGE_MAGICK_EXE, file_path, converted_path], check=True)
            print(f"Converted image saved to: {converted_path}")
            return converted_path
        except Exception as e:
            print(f"ImageMagick conversion failed: {e}")
            return file_path
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None

def extract_core_title_and_description(full_title, anime_titles):
    separators = [
        " Anime ", " Gets ", " Announces ", " Reveals ", " Confirmed ",
        " Premieres ", " Debuts ", " Trailer ", " English Dub "
    ]
    separator_pattern = '(' + '|'.join(map(re.escape, separators)) + ')'
    match = re.search(separator_pattern, full_title, flags=re.IGNORECASE)
    
    if match:
        core_title = full_title[:match.start()].strip()
        description = full_title[match.start():].strip()
    else:
        core_title = full_title.strip()
        description = ""
    
    print(f"Core Title for fuzzy matching: {core_title}")
    print(f"Extracted Description: {description}")
    
    match = process.extractOne(core_title, anime_titles, scorer=fuzz.partial_ratio)
    if match:
        title, score = match
        print(f"Matching {core_title} with AniList titles: {title} (Score: {score})")
        if score > 80:
            core_title = title
    else:
        print(f"No fuzzy match found for: {core_title}")
    
    return core_title, description

def get_first_post_if_anime(feed):
    """
    Returns the first entry in the feed if its category contains 'anime'.
    """
    if feed.entries:
        first = feed.entries[0]
        category = first.get("category", "").lower()
        if "anime" in category:
            return {
                "title": first.title,
                "link": first.link,
                "description": first.description,
                "pubDate": first.published,
                "category": first.get("category", ""),
            }
    return None

def save_to_json(data, filename="most_recent_post.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)
    print(f"Post saved to {filename}.")

try:
    print("Fetching RSS feed from Anime News Network...")
    feed = feedparser.parse("https://www.animenewsnetwork.com/newsroom/rss.xml")
    
    print("Checking the very first post for 'Anime' category...")
    recent_post = get_first_post_if_anime(feed)
    
    if recent_post:
        print("Fetching AniList titles and background image...")
        # First call using the post title
        anime_titles, image_url = fetch_anilist_titles_and_image(recent_post['title'])
        
        # Extract core title and description (this can be used to improve the title matching)
        core_title, description = extract_core_title_and_description(recent_post['title'], [])
        
        # Optionally, use the core title to query AniList again
        print("Fetching AniList titles and background image again using the core title...")
        anime_titles, image_url = fetch_anilist_titles_and_image(core_title)
        
        recent_post['title'] = core_title
        recent_post['description'] = description if description else recent_post['description']
        recent_post['image_url'] = image_url

        print("Extracted Post:")
        print(recent_post)
        save_to_json(recent_post, OUTPUT_JSON_FILE)
    else:
        print("The first post is not anime-related. Skipping.")
except Exception as e:
    print(f"Error: {e}")
