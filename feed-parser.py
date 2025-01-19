import feedparser
import json
from datetime import datetime

FEED_URL = "https://www.animenewsnetwork.com/newsroom/rss.xml"

def fetch_feed(url):
    feed = feedparser.parse(url)
    if feed.bozo:
        raise Exception("Error parsing RSS feed.")
    return feed

def get_most_recent_anime_post(feed):
    if not feed.entries:
        return None
    # Get the most recent post (assumes the feed is already sorted by date)
    most_recent_post = feed.entries[0]
    category = most_recent_post.get("category", "").lower()
    if "anime" in category:
        return {
            "title": most_recent_post.title,
            "link": most_recent_post.link,
            "description": most_recent_post.description,
            "pubDate": datetime.strptime(most_recent_post.published, "%a, %d %b %Y %H:%M:%S %z"),
            "category": category,
        }
    return None

def save_to_json(post, filename="most_recent_post.json"):
    with open(filename, "w", encoding="utf-8") as f:
        # Set ensure_ascii=False to preserve special characters
        json.dump(post, f, indent=4, ensure_ascii=False, default=str)

try:
    print("Fetching RSS feed...")
    feed = fetch_feed(FEED_URL)
    
    print("Extracting the most recent post...")
    recent_post = get_most_recent_anime_post(feed)
    
    if recent_post:
        print("Anime-related post found. Saving to JSON...")
        save_to_json(recent_post)
        print("Post saved successfully.")
    else:
        print("The most recent post is not anime-related. No data saved.")
    
    # Placeholder for Photoshop and Instagram integration
    print("Photoshop automation integration: Pending implementation.")
    print("Instagram posting integration: Pending implementation.")

except Exception as e:
    print(f"Error: {e}")
