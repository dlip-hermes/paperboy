# 🗞️🏃💨 Paperboy

Automated article discovery from [Karakeep](https://github.com/karakeep-app/karakeep) favorites — interest analysis, scoring, and preview delivery.

The `karakeep/` folder contains the Karakeep Hermes Agent skill (imported from [OpenClaw](https://github.com/karakeep-app/karakeep)) and is a dependency for Paperboy.

## Installation for Hermes Agent

Copy both skill folders to your Hermes skills directory:

```bash
cp -r paperboy ~/.hermes/skills/research/
cp -r karakeep ~/.hermes/skills/research/
```

## Features

- **Interest Analysis** — Extracts and ranks tags from your favorited bookmarks (frequency-weighted)
- **Recent Article Detection** — Finds articles bookmarked since the last run using Karakeep's `after:` date filter plus client-side validation
- **Tag-Based Scoring** — Scores articles by tag relevance with substring and word-overlap matching
- **Preview URL Generation** — Dashboard preview links for the top N scored articles (default: 10)

## How It Works

1. Fetches all favorited bookmarks from Karakeep
2. Extracts & ranks tags by frequency (excludes generic tags like "inbox")
3. Queries Karakeep for bookmarks created since the last run (`after:<timestamp>`)
4. Scores each new article against your interest tags
5. Outputs the top 10 with formatted title, summary, and preview URL
6. Saves the current time as the last run for next execution

## Standalone Usage

```bash
# Prerequisites
export KARAKEEP_SERVER_ADDR="https://your-karakeep-instance.example.com"
export KARAKEEP_API_KEY="your-api-key"

# Run
python3 paperboy/paperboy.py

# Or schedule with cron
0 7 * * * cd /path/to/repo && python3 paperboy/paperboy.py
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ARTICLES` | 10 | Maximum articles to deliver per run |
| `TOP_TAGS_LIMIT` | 8 | Number of interest tags to use for scoring |
| `EXCLUDED_TAGS` | `{'inbox'}` | Tags to ignore when ranking interests |
| State file | `~/.hermes/.paperboy/strategy_state.json` | Tracks last run time |

> **Tip:** Enable `INFERENCE_ENABLE_AUTO_SUMMARIZATION=true` in your Karakeep server config environment to automatically generate AI summaries for all bookmarks. Paperboy uses these summaries in its preview output — richer summaries mean better article previews.

## License

MIT