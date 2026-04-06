# AI Content Growth Agent — YouTube & Social Media Automation

An automated AI agent that researches trending topics, generates original video content, optimises for SEO, distributes across platforms, and learns from performance data to grow YouTube channels and social media presence continuously.

---

## Features

| Module | Responsibility |
|---|---|
| **Research Agent** | Trend analysis, content gap detection, idea generation |
| **Strategy Agent** | Weekly/monthly calendars, idea prioritisation, optimal post times |
| **Creation Agent** | Script writing (hook→value→payoff), visual direction, thumbnail concepts |
| **SEO Agent** | CTR-optimised titles, descriptions, tags, and hashtags |
| **Distribution Agent** | Multi-platform upload/scheduling (YouTube, TikTok, Instagram, Facebook, X) |
| **Tracking Agent** | Analytics collection, pattern extraction, feedback loops |
| **Monetization Agent** | Ad revenue keywords, affiliate recommendations, sponsorship targeting |

---

## Project Structure

```
ai_agent/
├── config.py               # Environment-based configuration
├── main.py                 # Orchestrator & CLI entry point
├── agents/
│   ├── research_agent.py   # Market research & trend analysis
│   ├── strategy_agent.py   # Content strategy & planning
│   ├── creation_agent.py   # Video creation pipeline
│   ├── seo_agent.py        # SEO & optimisation
│   ├── distribution_agent.py  # Automated distribution
│   ├── tracking_agent.py   # Performance tracking & learning
│   └── monetization_agent.py  # Monetisation strategy
├── models/
│   ├── content.py          # Content data models
│   └── analytics.py        # Analytics data models
└── utils/
    ├── llm.py              # OpenAI LLM client
    └── api_clients.py      # YouTube, TikTok, Instagram, Facebook, Twitter clients
tests/
├── test_models.py
├── test_llm_client.py
├── test_research_agent.py
├── test_strategy_agent.py
├── test_creation_agent.py
├── test_seo_agent.py
├── test_distribution_agent.py
├── test_tracking_agent.py
└── test_monetization_agent.py
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/CreatorX02/AI-AGENT-FOR-YOUTUBE-SOCIAL-MEDIA-AUTOMATION.git
cd AI-AGENT-FOR-YOUTUBE-SOCIAL-MEDIA-AUTOMATION
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

Required keys:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Content generation (GPT-4o) |
| `YOUTUBE_API_KEY` | Trend research & analytics |
| `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` | Video upload (OAuth) |
| `TIKTOK_ACCESS_TOKEN` | TikTok publishing |
| `INSTAGRAM_ACCESS_TOKEN` / `INSTAGRAM_ACCOUNT_ID` | Instagram Reels |
| `FACEBOOK_ACCESS_TOKEN` / `FACEBOOK_PAGE_ID` | Facebook video |
| `TWITTER_API_KEY` / `TWITTER_API_SECRET` / `TWITTER_ACCESS_TOKEN` / `TWITTER_ACCESS_SECRET` | X (Twitter) |

Optional settings:

```dotenv
TARGET_NICHES=finance,AI,technology,health,productivity
CONTENT_CYCLE_INTERVAL_HOURS=24
ANALYTICS_LOOKBACK_DAYS=30
```

### 3. Run a Single Cycle

```bash
python -m ai_agent.main
```

### 4. Run as a Continuous Daemon

```bash
python -m ai_agent.main --daemon
```

The daemon executes the full pipeline on the configured interval (`CONTENT_CYCLE_INTERVAL_HOURS`).

---

## Execution Cycle

```
Research → Analyse → Create → SEO → Monetise → Distribute → Track → Repeat
```

Each cycle:
1. **Research** — Fetches trending YouTube videos per niche; calls LLM for gap analysis.
2. **Strategy** — Scores and prioritises ideas; builds weekly content calendar.
3. **Creation** — Generates hook→body→CTA scripts, scene-by-scene visual directions, and thumbnail concepts.
4. **SEO** — Produces CTR-optimised titles, keyword-rich descriptions, tags, and hashtags.
5. **Monetisation** — Identifies high-RPM keywords, affiliate programs, and sponsorship categories.
6. **Distribution** — Builds platform-specific variants (aspect ratio, captions, hashtags). Uploads to YouTube when local file paths are provided; publishes to TikTok, Instagram, Facebook, and X when hosted video URLs are provided.
7. **Tracking** — Retrieves channel analytics; extracts top-performing patterns; generates strategic recommendations for the next cycle.

---

## Output: ContentPackage

Every content idea is wrapped in a `ContentPackage` containing:

- `idea` — original title, niche, hook, estimated RPM, priority score
- `script` — hook, body, CTA, estimated duration
- `visual_direction` — timestamped scenes with B-roll suggestions
- `thumbnail` — headline text, background, emotion, colour scheme
- `seo` — title, description, tags, hashtags
- `platform_variants` — per-platform captions and aspect ratios
- `monetization` — ad keywords, affiliates, digital products, sponsorships
- `youtube_video_id` — set after a successful YouTube upload

---

## Testing

```bash
python -m pytest tests/ -v
```

All 100 tests run without real API calls (all external services are mocked).

---

## Ethics & Constraints

- **No copyright infringement** — All content is generated originally using LLM prompts that explicitly prohibit copying.
- **No reused content penalties** — Scripts are fully original; the agent reverse-engineers *patterns*, not actual videos.
- **Platform policy compliance** — Monetisation eligibility guidelines are followed in all recommendations.
- **Secrets stay local** — API keys are loaded from `.env` only; never committed to source control.
