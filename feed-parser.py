import feedparser
import requests
from fuzzywuzzy import fuzz, process
import spacy
import json
import re

LOCAL_FEED_PATH = "rss.xml"
ANILIST_API_URL = "https://graphql.anilist.co"
OUTPUT_JSON_FILE = "most_recent_post.json"

nlp = spacy.load("en_core_web_sm")

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
        return titles, image_url
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    return [], None



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

def get_most_recent_anime_post(feed):
    for entry in feed.entries:
        category = entry.get("category", "").lower()
        if "anime" in category:
            return {
                "title": entry.title,
                "link": entry.link,
                "description": entry.description,
                "pubDate": entry.published,
                "category": category,
            }
    return None

def save_to_json(data, filename="most_recent_post.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, default=str)
    print(f"Post saved to {filename}.")

try:
    print("Parsing local RSS feed...")
    with open(LOCAL_FEED_PATH, "r", encoding="utf-8") as f:
        feed_content = f.read()
    
    feed = feedparser.parse(feed_content)
    
    print("Extracting the most recent anime post...")
    recent_post = get_most_recent_anime_post(feed)
    
    if recent_post:
        print("Fetching AniList titles and background image...")
        anime_titles, image_url = fetch_anilist_titles_and_image(recent_post['title'])
        
        core_title, description = extract_core_title_and_description(recent_post['title'], [])

        print("Fetching AniList titles and background image...")
        anime_titles, image_url = fetch_anilist_titles_and_image(core_title)

        recent_post['title'] = core_title
        recent_post['description'] = description if description else recent_post['description']
        recent_post['image_url'] = image_url

        print("Extracted Post:")
        print(recent_post)
        save_to_json(recent_post, OUTPUT_JSON_FILE)
    else:
        print("No anime-related post found.")
except Exception as e:
    print(f"Error: {e}")
