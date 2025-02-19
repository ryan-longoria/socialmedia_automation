"""
This script fetches the latest Anime-related post from the Anime News Network
RSS feed. If the first post is Anime-related, it queries the AniList API to
retrieve title information and cover image, downloads and converts the cover
image, and saves the post data to a JSON file.
"""

import feedparser
import requests
from fuzzywuzzy import fuzz, process
import os
import json
import re
import subprocess

ANILIST_API_URL = "https://graphql.anilist.com"
OUTPUT_JSON_FILE = "most_recent_post.json"

IMAGE_MAGICK_EXE = (
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
)


def fetch_anilist_titles_and_image(core_title):
    """
    Query the AniList API for an anime with the given title and retrieve
    its title variants and cover image.

    Parameters:
        core_title (str): The core title to search for.

    Returns:
        tuple: A tuple containing a list of title variants and the path
               to the downloaded (and converted) cover image.
    """
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
    variables = {"searchTitle": core_title}

    print("Sending request to AniList API with payload:")
    print(json.dumps({"query": query, "variables": variables}, indent=4))

    try:
        response = requests.post(
            ANILIST_API_URL, json={"query": query, "variables": variables}
        )
        response.raise_for_status()
        data = response.json()

        print("AniList API response:")
        print(json.dumps(data, indent=4))

        titles = []
        image_url = None
        if "Media" in data["data"]:
            media = data["data"]["Media"]
            titles.extend(
                filter(
                    None,
                    [
                        media["title"]["romaji"],
                        media["title"]["english"],
                        media["title"]["native"],
                    ],
                )
            )
            image_url = media["coverImage"]["extraLarge"]

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
    """
    Download an image from the provided URL and convert it to a proper JPEG
    using ImageMagick.

    Parameters:
        url (str): URL of the image to download.

    Returns:
        str or None: Path to the converted image file, or None if the download
                     fails or the image is incomplete.
    """
    file_path = os.path.join(os.getcwd(), "backgroundimage.jpg")
    try:
        print(f"Downloading image from: {url}")
        response = requests.get(
            url, stream=True, headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"Image saved to: {file_path}")

        file_size = os.path.getsize(file_path)
        print(f"Downloaded file size: {file_size} bytes")
        if file_size < 1000:
            print("Error: File size too small, likely incomplete.")
            return None

        converted_path = os.path.join(
            os.getcwd(), "backgroundimage_converted.jpg"
        )
        try:
            subprocess.run(
                [IMAGE_MAGICK_EXE, file_path, converted_path], check=True
            )
            print(f"Converted image saved to: {converted_path}")
            return converted_path
        except Exception as e:
            print(f"ImageMagick conversion failed: {e}")
            return file_path
    except Exception as e:
        print(f"Failed to download image: {e}")
        return None


def extract_core_title_and_description(full_title, anime_titles):
    """
    Extract the core title and description from the full title using common
    separators. Additionally, perform fuzzy matching with provided anime titles.

    Parameters:
        full_title (str): The full title string.
        anime_titles (list): List of known anime titles for fuzzy matching.

    Returns:
        tuple: A tuple containing the core title and the extracted description.
    """
    separators = [
        " Anime ", " Gets ", " Announces ", " Reveals ", " Confirmed ",
        " Premieres ", " Debuts ", " Trailer ", " English Dub "
    ]
    separator_pattern = "(" + "|".join(map(re.escape, separators)) + ")"
    match = re.search(separator_pattern, full_title, flags=re.IGNORECASE)

    if match:
        core_title = full_title[: match.start()].strip()
        description = full_title[match.start() :].strip()
    else:
        core_title = full_title.strip()
        description = ""

    print(f"Core Title for fuzzy matching: {core_title}")
    print(f"Extracted Description: {description}")

    match = process.extractOne(
        core_title, anime_titles, scorer=fuzz.partial_ratio
    )
    if match:
        title, score = match
        print(
            f"Matching {core_title} with AniList titles: {title} (Score: {score})"
        )
        if score > 80:
            core_title = title
    else:
        print(f"No fuzzy match found for: {core_title}")

    return core_title, description


def get_first_post_if_anime(feed):
    """
    Retrieve the first entry in the RSS feed if its category contains 'anime'.

    Parameters:
        feed (FeedParserDict): The parsed RSS feed.

    Returns:
        dict or None: A dictionary with the post details if the first post is
                      anime-related, or None otherwise.
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
    """
    Save the provided data to a JSON file.

    Parameters:
        data (dict): The data to save.
        filename (str): The output filename. Defaults to 'most_recent_post.json'.
    """
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)
    print(f"Post saved to {filename}.")


if __name__ == "__main__":
    try:
        print("Fetching RSS feed from Anime News Network...")
        feed = feedparser.parse(
            "https://www.animenewsnetwork.com/newsroom/rss.xml"
        )

        print("Checking the very first post for 'Anime' category...")
        recent_post = get_first_post_if_anime(feed)

        if recent_post:
            print("Fetching AniList titles and background image...")
            anime_titles, image_url = fetch_anilist_titles_and_image(
                recent_post["title"]
            )

            core_title, description = extract_core_title_and_description(
                recent_post["title"], []
            )

            print(
                "Fetching AniList titles and background image again using "
                "the core title..."
            )
            anime_titles, image_url = fetch_anilist_titles_and_image(core_title)

            recent_post["title"] = core_title
            recent_post["description"] = (
                description if description else recent_post["description"]
            )
            recent_post["image_url"] = image_url

            print("Extracted Post:")
            print(recent_post)
            save_to_json(recent_post, OUTPUT_JSON_FILE)
        else:
            print("The first post is not anime-related. Skipping.")
    except Exception as e:
        print(f"Error: {e}")
