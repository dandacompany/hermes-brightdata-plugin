# hermes-brightdata

Bright Data web data tools for Hermes Agent — search, scrape, structured datasets, and browser automation.

## Overview

This plugin integrates Bright Data's web data APIs with Hermes, providing nine powerful tools for web data collection:

- **Search & Scraping**: Real-time search, single/batch URL scraping, and structured data extraction
- **Browser Automation**: Interactive browser sessions with persistent cookies and JavaScript rendering
- **Bypass Detection**: Automatic handling of bot detection, CAPTCHAs, and JavaScript-heavy sites

Bright Data handles all the complexity — proxy rotation, header management, retry logic, and content parsing.

## Installation

Install the plugin with base tools:

```bash
pip install hermes-brightdata
```

To enable browser automation tools, install with the `[browser]` extra:

```bash
pip install hermes-brightdata[browser]
```

The browser extra adds Playwright for interactive session handling (required for `browser_navigate`, `browser_snapshot`, `browser_act`, `browser_get`).

## Configuration

Before using any Bright Data tool, set your API credentials in environment variables:

### Required

`BRIGHTDATA_API_TOKEN` (required, secret)

- Your Bright Data API token
- Obtain from Account Settings → API keys in the Bright Data dashboard
- `BRIGHTDATA_API_KEY` is accepted as an alias if `BRIGHTDATA_API_TOKEN` is unset

### Optional

`BRIGHTDATA_WEB_UNLOCKER_ZONE` (optional)

- Zone name for Web Unlocker API
- Default: `web_unlocker1`
- `WEB_UNLOCKER_ZONE` is accepted as an alias if the prefixed name is unset

`BRIGHTDATA_SERP_ZONE` (optional)

- Zone name for SERP (Search Engine Results Page) API
- Default: `serp_api1`

`BRIGHTDATA_BROWSER_AUTH` (optional, secret)

- Authentication credentials for Scraping Browser
- Format: `brd-customer-<customer-id>-zone-<zone-name>:<password>`
- Required only if using browser tools with authentication

### Example

```bash
export BRIGHTDATA_API_TOKEN="your-api-token-here"
export BRIGHTDATA_BROWSER_AUTH="brd-customer-12345-zone-myzone:password123"
```

## Tools

The plugin provides nine tools:

| Tool               | Description                                                                                                                                                                                                   |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_engine`    | Search the web via Bright Data SERP API and return parsed results. Use for current events, fact-checking, finding pages, or any web search. Bypasses bot detection; more reliable than built-in web search.   |
| `scrape`           | Fetch a single URL as clean markdown (or html) using Bright Data Web Unlocker. Handles JavaScript, CAPTCHAs, and bot detection. Use to read any webpage, article, doc, or site.                               |
| `scrape_batch`     | Scrape multiple URLs in one call (max 20). Returns per-URL content or error. Use when you have several pages to read at once.                                                                                 |
| `web_data`         | Get structured JSON data from a supported platform via Bright Data Web Scraper API (e.g. an Amazon product page, a LinkedIn profile). Returns clean structured fields, not raw HTML. May take up to a minute. |
| `session_stats`    | Report Bright Data tool call counts for this session.                                                                                                                                                         |
| `browser_navigate` | Open a URL in a Bright Data Scraping Browser (real browser with a persistent session). Use for interactive flows requiring clicks/typing. Requires the [browser] extra and BRIGHTDATA_BROWSER_AUTH.           |
| `browser_snapshot` | Return an accessibility-tree snapshot of the current browser page, including element refs to use with browser_act.                                                                                            |
| `browser_act`      | Perform an action on the current browser page: click, type, scroll, or wait. Get element refs from browser_snapshot first.                                                                                    |
| `browser_get`      | Read the current browser page: html, text, or a base64 screenshot.                                                                                                                                            |

## Activation

Enable the plugin in Hermes:

```bash
hermes plugins enable brightdata
```

Verify it's loaded:

```bash
hermes plugins list
```

You should see `brightdata` listed with version `0.1.0`.

## Pricing

Bright Data offers a free tier with up to 5,000 requests per month. For higher volume, refer to Bright Data's pricing page for details on Web Unlocker, SERP API, Web Scraper API, and Scraping Browser plans.

---

For more information on Bright Data services, visit [https://brightdata.com](https://brightdata.com).
