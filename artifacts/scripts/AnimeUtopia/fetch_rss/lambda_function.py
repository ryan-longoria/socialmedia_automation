import feedparser


def get_first_post_if_anime(feed):
    """Retrieve the first anime-related entry from the RSS feed.

    Args:
        feed (FeedParserDict): Parsed RSS feed.

    Returns:
        dict or None: Dictionary containing post details if the first entry
                      is anime-related; otherwise, None.
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
                "category": first.get("category", "")
            }
    return None


def lambda_handler(event, context):
    """Fetch the RSS feed and determine if the first post is anime-related.

    Args:
        event (dict): Lambda event data.
        context (object): Lambda context object.

    Returns:
        dict: Dictionary with a status and post details if an anime post is found.
    """
    feed_url = "https://www.animenewsnetwork.com/newsroom/rss.xml"
    feed = feedparser.parse(feed_url)
    recent_post = get_first_post_if_anime(feed)
    if recent_post:
        return {"status": "anime_post_found", "post": recent_post}
    return {"status": "no_post"}