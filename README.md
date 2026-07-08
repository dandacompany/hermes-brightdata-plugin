# hermes-brightdata

[![CI](https://github.com/dandacompany/hermes-brightdata-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/dandacompany/hermes-brightdata-plugin/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/hermes-brightdata.svg)](https://pypi.org/project/hermes-brightdata/)
[![Python](https://img.shields.io/pypi/pyversions/hermes-brightdata.svg)](https://pypi.org/project/hermes-brightdata/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Bright Data web data tools for [NousResearch Hermes Agent](https://hermes-agent.nousresearch.com) — web search, scraping, structured datasets, residential proxy, and browser automation, exposed as **ten native plugin tools**.

Pure Python (`requests` + optional `playwright`), no Node runtime. Unlike an MCP server, these tools are also available inside `delegate_task` subagents, which do not inherit the parent's MCP toolsets.

- [Why this plugin](#why-this-plugin)
- [Installation](#installation)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Tools](#tools)
- [Supported `web_data` platforms](#supported-web_data-platforms)
- [Development](#development)
- [Pricing](#pricing)

## Why this plugin

Bright Data handles the hard parts of web data collection — proxy rotation, header management, bot/CAPTCHA bypass, JavaScript rendering, and structured parsing. This plugin bridges all of that into Hermes as first-class tools:

- **Search & scrape** — real-time SERP search, single/batch URL scraping to clean markdown.
- **Structured datasets** — one `web_data` tool covers 23 platforms (Amazon, LinkedIn, Instagram, TikTok, Facebook, YouTube, X, Crunchbase) via a single `platform` parameter.
- **Residential proxy** — geo-targeted fetching through real residential IPs.
- **Browser automation** — a persistent CDP Scraping Browser session for interactive flows.

## Installation

Core tools (search, scrape, datasets, proxy):

```bash
pip install hermes-brightdata
```

Add the `[browser]` extra for browser automation (installs Playwright):

```bash
pip install "hermes-brightdata[browser]"
```

**Requirements:** Python 3.10+. The `browser_*` tools additionally require the `[browser]` extra and `BRIGHTDATA_BROWSER_AUTH`; the core five tools run on `requests` alone.

## Quick start

```bash
# 1. Set your Bright Data API token
export BRIGHTDATA_API_TOKEN="your-api-token-here"

# 2. Enable the plugin in Hermes
hermes plugins enable brightdata
```

The agent can now call the tools, e.g.:

- `scrape` → `{"url": "https://example.com"}`
- `search_engine` → `{"query": "bright data", "engine": "google"}`
- `web_data` → `{"platform": "amazon_product", "url": "https://www.amazon.com/dp/..."}`
- `proxy_scrape` → `{"url": "https://...", "country": "us"}`

Every tool returns a JSON string; failures come back as `{"error": ..., "hint": ...}` rather than raising.

## Configuration

Credentials are read from environment variables.

### Required

| Variable               | Notes                                                                                              |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| `BRIGHTDATA_API_TOKEN` | Bright Data API token (Account Settings → API keys). `BRIGHTDATA_API_KEY` is accepted as an alias. |

### Optional

| Variable                       | Purpose                                                                       | Default                   |
| ------------------------------ | ----------------------------------------------------------------------------- | ------------------------- |
| `BRIGHTDATA_WEB_UNLOCKER_ZONE` | Web Unlocker zone (alias: `WEB_UNLOCKER_ZONE`)                                | `web_unlocker1`           |
| `BRIGHTDATA_SERP_ZONE`         | SERP API zone                                                                 | `serp_api1`               |
| `BRIGHTDATA_BROWSER_AUTH`      | Scraping Browser auth `brd-customer-<id>-zone-<zone>:<password>`              | —                         |
| `BRIGHTDATA_PROXY_AUTH`        | Residential proxy auth `brd-customer-<id>-zone-<residential-zone>:<password>` | —                         |
| `BRIGHTDATA_PROXY_CA`          | Path to the Bright Data proxy CA cert (for HTTPS via proxy, port 33335)       | —                         |
| `BRIGHTDATA_PROXY_HOST`        | Proxy `host:port`                                                             | `brd.superproxy.io:33335` |

Example:

```bash
export BRIGHTDATA_API_TOKEN="your-api-token-here"
export BRIGHTDATA_BROWSER_AUTH="brd-customer-12345-zone-myzone:password123"
export BRIGHTDATA_PROXY_AUTH="brd-customer-12345-zone-residential:password123"
export BRIGHTDATA_PROXY_CA="/path/to/BrightData_proxy_ca.crt"
```

## Tools

| Tool               | Description                                                                                                                                                          |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_engine`    | Search the web via Bright Data SERP API and return parsed results. Bypasses bot detection; more reliable than a built-in web search.                                 |
| `scrape`           | Fetch a single URL as clean markdown (or html) using Web Unlocker. Handles JavaScript, CAPTCHAs, and bot detection.                                                  |
| `scrape_batch`     | Scrape multiple URLs in one call (max 20). Returns per-URL content or error, isolating individual failures.                                                          |
| `web_data`         | Get structured JSON from a supported platform via Web Scraper API (e.g. an Amazon product, a LinkedIn profile). Clean fields, not raw HTML. May take up to a minute. |
| `proxy_scrape`     | Fetch a URL through a residential proxy, optionally from a specific country. For geo-targeted content. Requires `BRIGHTDATA_PROXY_AUTH`.                             |
| `session_stats`    | Report Bright Data tool call counts for this session.                                                                                                                |
| `browser_navigate` | Open a URL in a Scraping Browser (persistent CDP session). Requires the `[browser]` extra and `BRIGHTDATA_BROWSER_AUTH`.                                             |
| `browser_snapshot` | Return an ARIA snapshot (accessibility tree) of the current page for reading its structure and content.                                                              |
| `browser_act`      | Perform an action on the current page: `click`, `type`, `scroll`, or `wait`. Target `click`/`type` with a CSS or text selector (e.g. `#submit`, `text=Login`).       |
| `browser_get`      | Read the current page: `html`, `text`, or a base64 `screenshot`.                                                                                                     |

The Scraping Browser session is created lazily on the first `browser_navigate` and closed automatically on session end.

## Supported `web_data` platforms

Pass one of these as the `platform` argument (all take a URL):

| Group       | Platforms                                                                                 |
| ----------- | ----------------------------------------------------------------------------------------- |
| Amazon      | `amazon_product`, `amazon_product_reviews`, `amazon_product_search`, `amazon_seller_info` |
| LinkedIn    | `linkedin_person`, `linkedin_company`, `linkedin_job_listings`, `linkedin_posts`          |
| Instagram   | `instagram_profile`, `instagram_posts`, `instagram_reels`, `instagram_comments`           |
| TikTok      | `tiktok_profiles`, `tiktok_posts`, `tiktok_comments`                                      |
| Facebook    | `facebook_posts`, `facebook_profiles`                                                     |
| YouTube     | `youtube_videos`, `youtube_profiles`, `youtube_comments`                                  |
| X (Twitter) | `x_posts`, `x_profile_posts`                                                              |
| Business    | `crunchbase_company`                                                                      |

An unknown platform returns an error listing the available ones.

## Development

```bash
git clone https://github.com/dandacompany/hermes-brightdata-plugin
cd hermes-brightdata-plugin
pip install -e ".[dev]"
pytest
```

CI runs the suite across Python 3.10–3.13 on every push. The plugin is organized as thin handlers (`tools.py`) over focused domain modules (`api.py`, `browser.py`, `datasets.py`, `config.py`, `counter.py`); each handler always returns a JSON string, accepts `**kwargs`, and never propagates exceptions.

## Pricing

Bright Data offers a free tier (up to 5,000 requests/month). See Bright Data's pricing for Web Unlocker, SERP API, Web Scraper API, residential proxy, and Scraping Browser plans.

---

Links: [PyPI](https://pypi.org/project/hermes-brightdata/) · [GitHub](https://github.com/dandacompany/hermes-brightdata-plugin) · [Bright Data](https://brightdata.com)
