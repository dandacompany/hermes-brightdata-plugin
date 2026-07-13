# hermes-brightdata

**Bright Data web data tools for [NousResearch Hermes Agent](https://hermes-agent.nousresearch.com) — search, scrape, structured datasets, residential proxy, and browser automation.**

[![CI](https://github.com/dandacompany/hermes-brightdata-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/dandacompany/hermes-brightdata-plugin/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/hermes-brightdata.svg)](https://pypi.org/project/hermes-brightdata/)
[![Python](https://img.shields.io/pypi/pyversions/hermes-brightdata.svg)](https://pypi.org/project/hermes-brightdata/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

한국어 문서: [README.ko.md](./README.ko.md)

This plugin exposes Bright Data's web data platform as **ten native Hermes tools**. Unlike an MCP server, these tools are also available inside `delegate_task` subagents, which do not inherit the parent's MCP toolsets. It is pure Python (`requests` + optional `playwright`) with no Node runtime.

Bright Data handles the hard parts of web data collection — proxy rotation, header management, bot/CAPTCHA bypass, JavaScript rendering, and structured parsing. The plugin keeps handlers thin over focused domain modules, so each tool is a small, testable surface.

## Why this plugin

- **Search & scrape** — real-time SERP search, and single/batch URL scraping to clean markdown via Web Unlocker.
- **Structured datasets** — one `web_data` tool covers 23 platforms (Amazon, LinkedIn, Instagram, TikTok, Facebook, YouTube, X, Crunchbase) through a single `platform` argument.
- **Residential proxy** — geo-targeted fetching through real residential IPs.
- **Browser automation** — a persistent CDP Scraping Browser session for interactive flows.

## Requirements

- Python 3.10+
- A Bright Data account and API token (`BRIGHTDATA_API_TOKEN`)
- For `brightdata_browser_*` tools: the `[browser]` extra (Playwright) and `BRIGHTDATA_BROWSER_AUTH`. The core five tools run on `requests` alone.

## Install

### Option A — pip (recommended)

The plugin ships on PyPI and registers with Hermes via an entry point:

```bash
pip install hermes-brightdata            # core tools
pip install "hermes-brightdata[browser]" # + browser automation (Playwright)
```

### Option B — from source

```bash
git clone https://github.com/dandacompany/hermes-brightdata-plugin ~/src/hermes-brightdata-plugin
cd ~/src/hermes-brightdata-plugin
pip install -e ".[browser]"
```

### Verify

```bash
hermes plugins list             # brightdata appears, not enabled (opt-in by default)
hermes plugins enable brightdata
```

Answer `no` to any tool-override prompt. Restart the gateway (`hermes gateway restart`) or `/reset` a session if the tools do not appear immediately.

## Set up Bright Data in Hermes

Install the package in the same Python environment that runs `hermes`, then
enable the opt-in plugin:

```bash
python -m pip install hermes-brightdata
hermes plugins enable brightdata
```

For browser automation, install the extra instead:

```bash
python -m pip install "hermes-brightdata[browser]"
```

The plugin adds standalone Bright Data tools on every supported Hermes release.
Hermes versions with the Web Search Provider API also register `brightdata` as a
native `web_search` backend; it never replaces Hermes' built-in tools.

### Configure through the setup wizard

This is the easiest way to persist the token in Hermes' environment file and
select Bright Data from the provider picker.

```bash
hermes setup tools
```

In the interactive UI, choose:

1. **Reconfigure an existing tool's provider or API key**
2. **Web Search & Scraping**
3. **Bright Data [paid]**
4. Paste the Bright Data API token when prompted.

The wizard configures Bright Data as the shared web backend. Bright Data's
provider implementation is search-only, so use the per-capability
`web.search_backend` override in the next section when another provider should
handle native extraction.

### Configure manually

For a one-off terminal session, export the token and select the native search
backend explicitly:

```bash
export BRIGHTDATA_API_TOKEN="your-api-token-here"
hermes config set web.search_backend brightdata
hermes config check
```

To persist the token, run `hermes config env-path`, open the reported file, and
add `BRIGHTDATA_API_TOKEN=...` there. Keep tokens out of shell history, source
control, prompts, and README examples. The plugin also accepts
`BRIGHTDATA_API_KEY`, or one unambiguous secret-manager label such as
`BRIGHTDATA_TEAM_TOKEN`.

`web.search_backend` is the recommended setting for this plugin. It takes
precedence over the shared `web.backend` value for native search, while leaving
the extraction backend under your existing configuration. Check the resulting
configuration at any time with `hermes config show`.

### Use it in a Hermes session

Start a fresh session after enabling the plugin or changing its backend:

```bash
hermes
```

Ask Hermes to use the native search capability, for example:

> Use native `web_search` to find the official OpenAI API documentation. Return the first three results with titles and URLs.

For script-friendly verification, run:

```bash
hermes -z "Use native web_search exactly once to search for OpenAI API documentation. Return the first result title and URL."
```

In an already-running interactive session, run `/reset` after the configuration
change. For gateway-based sessions, run `hermes gateway restart`. The standalone
tools remain available for Bright Data-specific work; ask Hermes to use one by
name when needed:

- `scrape` → `{"url": "https://example.com"}`
- `search_engine` → `{"query": "bright data", "engine": "google"}`
- `web_data` → `{"platform": "amazon_product", "url": "https://www.amazon.com/dp/..."}`
- `proxy_scrape` → `{"url": "https://...", "country": "us"}`

Every tool returns a JSON string; failures come back as `{"error": ..., "hint": ...}` rather than raising.

## Tools

| Tool                          | What it does                                                   | Notes                                                                       |
| ----------------------------- | -------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `search_engine`               | Web search via Bright Data SERP API, returning parsed results  | Bypasses bot detection; more reliable than a built-in web search            |
| `scrape`                      | Fetch a single URL as clean markdown or html                   | Web Unlocker — handles JS, CAPTCHAs, bot detection                          |
| `scrape_batch`                | Scrape multiple URLs in one call (max 20)                      | Per-URL content or error; individual failures are isolated                  |
| `web_data`                    | Structured JSON from a supported platform                      | Web Scraper API — clean fields, not raw HTML; may take up to a minute       |
| `proxy_scrape`                | Fetch a URL through a residential proxy, optionally by country | Requires `BRIGHTDATA_PROXY_AUTH`                                            |
| `session_stats`               | Report Bright Data tool call counts for this session           | —                                                                           |
| `brightdata_browser_navigate` | Open a URL in a Scraping Browser (persistent CDP session)      | Requires the `[browser]` extra and `BRIGHTDATA_BROWSER_AUTH`                |
| `brightdata_browser_snapshot` | ARIA snapshot (accessibility tree) of the current page         | For reading page structure and content                                      |
| `brightdata_browser_act`      | `click`, `type`, `scroll`, or `wait` on the current page       | Target `click`/`type` with a CSS or text selector (`#submit`, `text=Login`) |
| `brightdata_browser_get`      | Read the current page: `html`, `text`, or base64 screenshot    | —                                                                           |

The Scraping Browser session is created lazily on the first `brightdata_browser_navigate` and closed automatically on session end. The `brightdata_` prefix prevents collisions with Hermes' built-in browser tools.

### Supported `web_data` platforms

Pass one as the `platform` argument (all take a URL); an unknown value returns an error listing the available ones.

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

## Configuration

Credentials are read from environment variables.

**Required**

| Variable               | Notes                                                                                                                                                                        |
| ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BRIGHTDATA_API_TOKEN` | Bright Data API token (Account Settings → API keys). `BRIGHTDATA_API_KEY`, or one unambiguous secret-manager label such as `BRIGHTDATA_TEAM_TOKEN`, is accepted as an alias. |

**Optional**

| Variable                       | Purpose                                                                       | Default                   |
| ------------------------------ | ----------------------------------------------------------------------------- | ------------------------- |
| `BRIGHTDATA_WEB_UNLOCKER_ZONE` | Web Unlocker zone (alias: `WEB_UNLOCKER_ZONE`)                                | `web_unlocker1`           |
| `BRIGHTDATA_SERP_ZONE`         | SERP API zone                                                                 | `serp_api1`               |
| `BRIGHTDATA_BROWSER_AUTH`      | Scraping Browser auth `brd-customer-<id>-zone-<zone>:<password>`              | —                         |
| `BRIGHTDATA_PROXY_AUTH`        | Residential proxy auth `brd-customer-<id>-zone-<residential-zone>:<password>` | —                         |
| `BRIGHTDATA_PROXY_CA`          | Path to the Bright Data proxy CA cert (HTTPS via proxy, port 33335)           | —                         |
| `BRIGHTDATA_PROXY_HOST`        | Proxy `host:port`                                                             | `brd.superproxy.io:33335` |

## Development

```bash
git clone https://github.com/dandacompany/hermes-brightdata-plugin
cd hermes-brightdata-plugin
pip install -e ".[dev]"
pytest
```

CI runs the suite across Python 3.10–3.13 on every push. The plugin is organized as thin handlers (`tools.py`) over focused domain modules (`api.py`, `browser.py`, `datasets.py`, `config.py`, `counter.py`). Every handler follows the same contract: it always returns a JSON string, accepts `**kwargs`, and never propagates exceptions.

## Security

The plugin talks to Bright Data over HTTPS and, in browser/proxy modes, drives a remote browser and a residential proxy. Handling of that surface:

- **Credentials never leak into output.** API errors carry only status codes and hints; response bodies and the token are never serialized. On a browser connection failure the raw exception (which can embed the CDP URL, including the proxy password) is replaced with a scrubbed message.
- **Proxy `country` is validated.** The `country` argument is LLM-supplied and is inserted into the proxy URL's userinfo section, so it is strictly validated as a 2-letter ISO code and the userinfo is URL-encoded — a value like `us:pw@evil` cannot break out and redirect credentials.
- **HTTPS through the proxy is verified against the Bright Data CA.** OpenSSL 3's strict Authority-Key-Identifier check (which the Bright Data proxy CA cert lacks) is relaxed, but the certificate chain is still validated against the provided CA — not disabled.

## License

[MIT](./LICENSE) © Dante Labs

---

<div align="center">

**Dante Labs** · **YouTube** [@dante-labs](https://youtube.com/@dante-labs) · **Email** [dante@dante-labs.com](mailto:dante@dante-labs.com) · **Discord** [Dante Labs Community](https://discord.com/invite/rXyy5e9ujs) · **Support** [Buy Me a Coffee](https://buymeacoffee.com/dante.labs)

</div>
