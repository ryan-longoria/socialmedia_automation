import json
import os
import re
import subprocess
import requests
from fuzzywuzzy import fuzz, process

ANILIST_API_URL = "https://graphql.anilist.com"
IMAGE_MAGICK_EXE = (
    r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
)


def fetch_anilist_titles_and_image(core_title):
    """Query the AniList API for an anime with the given title and retrieve
    title variants and the cover image.

    Args:
        core_title (str): The core title to search for.

    Returns:
        tuple: A tuple containing a list of title variants and the path to the
               downloaded (and converted) cover image.
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
                        media["title"].get("romaji"),
                        media["title"].get("english"),
                        media["title"].get("native"),
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
    """Download an image from the provided URL and convert it to a proper JPEG
    using ImageMagick.

    Args:
        url (str): URL of the image to download.

    Returns:
        str or None: Path to the converted image file, or None if the download
                     fails or the image is incomplete.
    """
    file_path = os.path.join(os.getcwd(), "backgroundimage.jpg")
    try:
        print(f"Downloading image from: {url}")
        response = requests.get(url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
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

        converted_path = os.path.join(os.getcwd(), "backgroundimage_converted.jpg")
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
    """Extract the core title and description from the full title using common
    separators and fuzzy matching.

    Args:
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
        core_title = full_title[:match.start()].strip()
        description = full_title[match.start():].strip()
    else:
        core_title = full_title.strip()
        description = ""

    print(f"Core Title for fuzzy matching: {core_title}")
    print(f"Extracted Description: {description}")

    match_result = process.extractOne(core_title, anime_titles, scorer=fuzz.partial_ratio)
    if match_result:
        title, score = match_result
        print(f"Matching {core_title} with AniList titles: {title} (Score: {score})")
        if score > 80:
            core_title = title
    else:
        print(f"No fuzzy match found for: {core_title}")

    return core_title, description


def lambda_handler(event, context):
    """Process the content of an anime post by querying AniList and downloading an image.

    Args:
        event (dict): Event data containing a 'post' key with post details.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary with the processed post details.
    """
    post = event.get("post", {})
    full_title = post.get("title", "")

    # First call using the raw title (for logging or initial query)
    _, _ = fetch_anilist_titles_and_image(full_title)

    # Refine the title and description
    core_title, description = extract_core_title_and_description(full_title, [])

    # Second call with the refined title to get image and title variants
    anime_titles, image_path = fetch_anilist_titles_and_image(core_title)

    post["title"] = core_title
    post["description"] = description if description else post.get("description", "")
    post["image_path"] = image_path

    return {"status": "processed", "post": post}
