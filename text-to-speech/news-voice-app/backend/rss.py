import hashlib
import re
from datetime import datetime, timezone

import feedparser

RSS_FEEDS = {
    "BBC World":  "http://feeds.bbci.co.uk/news/world/rss.xml",
    "NPR":        "https://feeds.npr.org/1001/rss.xml",
    "Guardian":   "https://www.theguardian.com/world/rss",
    "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
}


def _article_id(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _extract_image(entry) -> str | None:
    # media:content
    media = entry.get("media_content", [])
    for m in media:
        url = m.get("url", "")
        if url and any(url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
            return url
    # enclosure
    for enc in entry.get("enclosures", []):
        if enc.get("type", "").startswith("image/"):
            return enc.get("href") or enc.get("url")
    # media:thumbnail
    thumb = entry.get("media_thumbnail", [])
    if thumb:
        return thumb[0].get("url")
    return None


def fetch_articles(known_urls: set[str]) -> list[dict]:
    now = datetime.now(timezone.utc)
    results = []

    for source, feed_url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
        except Exception:
            continue

        for entry in feed.entries:
            url = entry.get("link", "").strip()
            if not url or url in known_urls:
                continue

            title = _strip_html(entry.get("title", ""))
            if not title:
                continue

            summary = _strip_html(entry.get("summary", entry.get("description", "")))[:400]

            published_at = None
            parsed = entry.get("published_parsed")
            if parsed:
                try:
                    published_at = datetime(*parsed[:6], tzinfo=timezone.utc).isoformat()
                except Exception:
                    pass

            results.append({
                "id":           _article_id(url),
                "title":        title,
                "summary":      summary,
                "url":          url,
                "image_url":    _extract_image(entry),
                "source":       source,
                "published_at": published_at,
                "fetched_at":   now.isoformat(),
            })

    return results
