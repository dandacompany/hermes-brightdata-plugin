# hermes-brightdata

**[NousResearch Hermes Agent](https://hermes-agent.nousresearch.com)용 Bright Data 웹 데이터 툴 — 검색, 스크레이핑, 구조화 데이터셋, residential 프록시, 브라우저 자동화.**

[![CI](https://github.com/dandacompany/hermes-brightdata-plugin/actions/workflows/ci.yml/badge.svg)](https://github.com/dandacompany/hermes-brightdata-plugin/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/hermes-brightdata.svg)](https://pypi.org/project/hermes-brightdata/)
[![Python](https://img.shields.io/pypi/pyversions/hermes-brightdata.svg)](https://pypi.org/project/hermes-brightdata/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

English: [README.md](./README.md)

Bright Data 웹 데이터 플랫폼을 **Hermes 네이티브 툴 10개**로 노출하는 플러그인이다. MCP 서버와 달리, 이 툴들은 부모의 MCP 툴셋을 상속받지 못하는 `delegate_task` 서브에이전트 안에서도 사용할 수 있다. 순수 Python(`requests` + 선택적 `playwright`)이라 Node 런타임이 필요 없다.

Bright Data가 웹 데이터 수집의 어려운 부분(프록시 로테이션, 헤더 관리, 봇·CAPTCHA 우회, JavaScript 렌더링, 구조화 파싱)을 처리한다. 플러그인은 얇은 핸들러를 도메인 모듈 위에 얹어, 각 툴을 작고 테스트하기 쉬운 표면으로 유지한다.

## 왜 이 플러그인인가

- **검색·스크레이핑** — 실시간 SERP 검색, Web Unlocker로 단일/배치 URL을 깨끗한 마크다운으로.
- **구조화 데이터셋** — `web_data` 툴 하나가 `platform` 인자로 23종(Amazon·LinkedIn·Instagram·TikTok·Facebook·YouTube·X·Crunchbase)을 커버.
- **residential 프록시** — 실제 residential IP로 지역 타겟팅 fetch.
- **브라우저 자동화** — 상호작용 흐름을 위한 지속 CDP Scraping Browser 세션.

## 요구사항

- Python 3.10+
- Bright Data 계정 및 API 토큰(`BRIGHTDATA_API_TOKEN`)
- `browser_*` 툴: `[browser]` extra(Playwright) + `BRIGHTDATA_BROWSER_AUTH`. 코어 5종은 `requests`만으로 동작.

## 설치

### Option A — pip (권장)

PyPI로 배포되며 entry point로 Hermes에 등록된다:

```bash
pip install hermes-brightdata            # 코어 툴
pip install "hermes-brightdata[browser]" # + 브라우저 자동화(Playwright)
```

### Option B — 소스에서

```bash
git clone https://github.com/dandacompany/hermes-brightdata-plugin ~/src/hermes-brightdata-plugin
cd ~/src/hermes-brightdata-plugin
pip install -e ".[browser]"
```

### 확인

```bash
hermes plugins list             # brightdata 표시, 기본은 비활성(opt-in)
hermes plugins enable brightdata
```

tool-override 프롬프트는 `no`로. 툴이 바로 안 보이면 게이트웨이 재시작(`hermes gateway restart`) 또는 세션 `/reset`.

## 빠른 시작

```bash
export BRIGHTDATA_API_TOKEN="발급받은-API-토큰"
hermes plugins enable brightdata
```

이제 에이전트가 툴을 호출할 수 있다. 인자 예시:

- `scrape` → `{"url": "https://example.com"}`
- `search_engine` → `{"query": "bright data", "engine": "google"}`
- `web_data` → `{"platform": "amazon_product", "url": "https://www.amazon.com/dp/..."}`
- `proxy_scrape` → `{"url": "https://...", "country": "us"}`

모든 툴은 JSON 문자열을 반환하며, 실패는 예외 대신 `{"error": ..., "hint": ...}`로 돌아온다.

## 툴

| 툴                 | 하는 일                                             | 비고                                                        |
| ------------------ | --------------------------------------------------- | ----------------------------------------------------------- |
| `search_engine`    | SERP API로 웹 검색, 파싱된 결과 반환                | 봇 탐지 우회, 내장 웹검색보다 안정적                        |
| `scrape`           | 단일 URL을 깨끗한 마크다운/html로                   | Web Unlocker — JS·CAPTCHA·봇탐지 처리                       |
| `scrape_batch`     | 여러 URL을 한 번에(최대 20)                         | URL별 결과/에러, 개별 실패 격리                             |
| `web_data`         | 지원 플랫폼의 구조화 JSON                           | Web Scraper API — raw HTML 아닌 정제 필드, 최대 1분 소요    |
| `proxy_scrape`     | residential 프록시 경유 fetch(국가 선택)            | `BRIGHTDATA_PROXY_AUTH` 필요                                |
| `session_stats`    | 이 세션의 툴 호출 수 보고                           | —                                                           |
| `browser_navigate` | Scraping Browser로 URL 열기(지속 CDP 세션)          | `[browser]` extra + `BRIGHTDATA_BROWSER_AUTH` 필요          |
| `browser_snapshot` | 현재 페이지의 ARIA 스냅샷(접근성 트리)              | 페이지 구조·내용 읽기용                                     |
| `browser_act`      | 현재 페이지에 `click`/`type`/`scroll`/`wait`        | `click`/`type`은 CSS·text 셀렉터로(`#submit`, `text=Login`) |
| `browser_get`      | 현재 페이지 읽기: `html`/`text`/base64 `screenshot` | —                                                           |

Scraping Browser 세션은 첫 `browser_navigate`에서 lazy 생성되고 세션 종료 시 자동으로 닫힌다.

### 지원 `web_data` 플랫폼

`platform` 인자로 아래 중 하나를 넘긴다(모두 URL 입력). 미지 값은 사용 가능 목록과 함께 에러를 반환한다.

| 그룹        | 플랫폼                                                                                    |
| ----------- | ----------------------------------------------------------------------------------------- |
| Amazon      | `amazon_product`, `amazon_product_reviews`, `amazon_product_search`, `amazon_seller_info` |
| LinkedIn    | `linkedin_person`, `linkedin_company`, `linkedin_job_listings`, `linkedin_posts`          |
| Instagram   | `instagram_profile`, `instagram_posts`, `instagram_reels`, `instagram_comments`           |
| TikTok      | `tiktok_profiles`, `tiktok_posts`, `tiktok_comments`                                      |
| Facebook    | `facebook_posts`, `facebook_profiles`                                                     |
| YouTube     | `youtube_videos`, `youtube_profiles`, `youtube_comments`                                  |
| X (Twitter) | `x_posts`, `x_profile_posts`                                                              |
| Business    | `crunchbase_company`                                                                      |

## 설정

자격증명은 환경변수에서 읽는다.

**필수**

| 변수                   | 비고                                                                                     |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| `BRIGHTDATA_API_TOKEN` | Bright Data API 토큰(Account Settings → API keys). `BRIGHTDATA_API_KEY`도 별칭으로 허용. |

**선택**

| 변수                           | 용도                                                                           | 기본값                    |
| ------------------------------ | ------------------------------------------------------------------------------ | ------------------------- |
| `BRIGHTDATA_WEB_UNLOCKER_ZONE` | Web Unlocker zone(별칭: `WEB_UNLOCKER_ZONE`)                                   | `web_unlocker1`           |
| `BRIGHTDATA_SERP_ZONE`         | SERP API zone                                                                  | `serp_api1`               |
| `BRIGHTDATA_BROWSER_AUTH`      | Scraping Browser 인증 `brd-customer-<id>-zone-<zone>:<password>`               | —                         |
| `BRIGHTDATA_PROXY_AUTH`        | residential 프록시 인증 `brd-customer-<id>-zone-<residential-zone>:<password>` | —                         |
| `BRIGHTDATA_PROXY_CA`          | Bright Data 프록시 CA 인증서 경로(포트 33335 HTTPS용)                          | —                         |
| `BRIGHTDATA_PROXY_HOST`        | 프록시 `host:port`                                                             | `brd.superproxy.io:33335` |

## 개발

```bash
git clone https://github.com/dandacompany/hermes-brightdata-plugin
cd hermes-brightdata-plugin
pip install -e ".[dev]"
pytest
```

CI가 매 푸시마다 Python 3.10–3.13에서 스위트를 실행한다. 플러그인은 얇은 핸들러(`tools.py`)를 도메인 모듈(`api.py`, `browser.py`, `datasets.py`, `config.py`, `counter.py`) 위에 얹은 구조다. 모든 핸들러는 동일한 규약을 따른다 — 항상 JSON 문자열 반환, `**kwargs` 수용, 예외 무전파.

## 보안

플러그인은 Bright Data와 HTTPS로 통신하고, 브라우저·프록시 모드에서는 원격 브라우저와 residential 프록시를 구동한다. 그 표면의 처리:

- **자격증명이 출력에 새지 않는다.** API 에러는 상태코드·힌트만 담고 응답 본문·토큰은 직렬화하지 않는다. 브라우저 연결 실패 시 원문 예외(프록시 비밀번호가 포함된 CDP URL이 박힐 수 있음)를 스크럽된 메시지로 교체한다.
- **프록시 `country`를 검증한다.** LLM이 넘기는 `country`는 프록시 URL의 userinfo에 삽입되므로 2자리 ISO 코드로 엄격 검증하고 userinfo를 URL 인코딩한다 — `us:pw@evil` 같은 값이 탈출해 자격증명을 리다이렉트할 수 없다.
- **프록시 경유 HTTPS는 Bright Data CA로 검증한다.** OpenSSL 3의 strict Authority-Key-Identifier 검사(Bright Data 프록시 CA 인증서에 없음)만 완화하되, 인증서 체인은 제공된 CA로 여전히 검증한다 — 비활성화가 아니다.

## 라이선스

[MIT](./LICENSE) © Dante Labs

---

<div align="center">

**Dante Labs** · **YouTube** [@dante-labs](https://youtube.com/@dante-labs) · **Email** [dante@dante-labs.com](mailto:dante@dante-labs.com) · **Discord** [Dante Labs Community](https://discord.com/invite/rXyy5e9ujs) · **Support** [Buy Me a Coffee](https://buymeacoffee.com/dante.labs)

</div>
