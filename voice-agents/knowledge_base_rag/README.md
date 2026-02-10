# Knowledge Base RAG

Create and populate Knowledge Bases for RAG-powered agents.

## Features

- **PDF Upload** — Upload PDF files via API
- **URL Scraping** — Scrape web pages via API
- **KB Management** — Create, list, get, delete Knowledge Bases
- **Item Status Tracking** — Monitor processing status of uploaded content

## Requirements

> Base dependencies are installed via the root `requirements.txt`. See the [main README](../../README.md#usage) for setup. Add `SMALLEST_API_KEY` to your `.env`.

Extra dependencies:

```bash
uv pip install -r requirements.txt
```

This installs `reportlab` for PDF generation in the demo script.

## Usage

```bash
uv run setup_kb.py
```

## Recommended Usage

- Giving your voice agent access to custom documents and web content for RAG-powered answers
- PDF upload, URL scraping, and KB lifecycle management via API

## Key Snippets

### PDF Upload

```python
from smallestai.atoms import KB

kb = KB()

# Create KB
result = kb.create(name="My KB", description="My docs")
kb_id = result["data"]["_id"]

# Upload PDF
kb.add_file(kb_id, "document.pdf")

# Check status
items = kb.get_items(kb_id)
for item in items["data"]:
    print(f"{item['fileName']}: {item['processingStatus']}")
```

### URL Scraping

```python
from smallestai.atoms import KB

kb = KB()

# Create KB
result = kb.create(name="My KB")
kb_id = result["data"]["_id"]

# Scrape URLs
kb.scrape_urls(kb_id, [
    "https://example.com/docs",
    "https://example.com/faq"
])

# Check status
scraped = kb.get_scraped_urls(kb_id)
```

### KB Management

```python
kb = KB()

# List all KBs
kb.list()

# Get KB details  
kb.get(kb_id)

# Get items
kb.get_items(kb_id)

# Delete KB
kb.delete(kb_id)
```

## Notes

- Only PDF files are supported for upload
- Text upload is not yet available via API (use dashboard)
- Link KB to agent via `globalKnowledgeBaseId` in dashboard

## API Reference

- [Atoms SDK — Quick Start](https://atoms-docs.smallest.ai/dev/introduction/quickstart)

## Next Steps

- Link the KB to your agent in the dashboard to enable RAG
- See [Agent with Tools](../agent_with_tools/) for adding function tools alongside KB
