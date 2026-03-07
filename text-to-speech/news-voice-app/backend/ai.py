import json
import re

from openai import OpenAI

_client: OpenAI | None = None


def _get_client(api_key: str) -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=api_key)
    return _client


def group_articles(articles: list[dict], api_key: str) -> list[dict]:
    """
    Send article titles to GPT-4o-mini and get back event groupings.
    Returns: [{"name": str, "article_ids": [str, ...]}]
    """
    if not articles:
        return []

    client = _get_client(api_key)

    lines = "\n".join(f"{i}. [{a['source']}] {a['title']}" for i, a in enumerate(articles))

    prompt = f"""You are a news editor. Group the following headlines into major story clusters.
Each headline belongs to exactly one cluster. Aim for 6-12 clusters covering the biggest stories.

Return ONLY a JSON array with no markdown, no explanation:
[{{"name": "Short group name (max 6 words)", "indices": [0, 3, 7]}}]

Headlines:
{lines}"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )

    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)

    groups_raw = json.loads(raw)
    result = []
    for g in groups_raw:
        ids = [articles[i]["id"] for i in g["indices"] if i < len(articles)]
        if ids:
            result.append({"name": g["name"], "article_ids": ids})
    return result


def summarize_group(group_name: str, articles: list[dict], api_key: str) -> str:
    """
    Generate a 2-3 minute broadcast script for the given group of articles.
    """
    client = _get_client(api_key)

    context = "\n\n".join(
        f"[{a['source']}] {a['title']}\n{a.get('summary', '')}" for a in articles
    )

    prompt = f"""You are a news summarizer. Write a clear, third-person summary (~350-400 words) of the following story: "{group_name}"

Rules:
- Write in third person throughout (he, she, they, officials, the government, etc.)
- Do NOT open with phrases like "This is...", "Good day", "Welcome to...", "In today's news", or any broadcaster introduction
- Do NOT use "I", "we", or address the listener directly
- Start immediately with the substance of the news (who did what, what happened, what was announced)
- Use a neutral, factual tone — report what happened, attribute claims to sources
- No stage directions, no section headers, no brackets

Source material:
{context}"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    return resp.choices[0].message.content.strip()
