---
name: paperboy
description: Automated workflow to discover articles based on favorited Karakeep bookmarks and deliver them via dashboard preview links with title, summary, and link — named "🏃💨 Paperboy Run! 🗞️" because it delivers your news every day.
version: 2.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [automation, karakeep, bookmarks, discovery, productivity]
    related_skills: [karakeep]
---

# Article Discovery and Delivery Workflow

## Overview

The 🏃💨 Paperboy Run! 🗞️ workflow focuses on discovering recent articles from your Karakeep account based on your favorited bookmarks and delivering them with title, summary, and link:

1. **Interest Analysis**: Extracts and analyzes tags from favorited bookmarks to determine current interests
2. **Recent Article Detection**: Finds articles added to Karakeep since the last run using date-based search
3. **Tag-Based Scoring**: Scores articles based on tag relevance from favorited bookmarks (with frequency weighting)
4. **Link Generation**: Generates dashboard preview URLs for the top N scored articles (default: 10)
5. **Detailed Output**: Outputs title, summary, and link for each article
6. **Automation**: Runs automatically via cron job to deliver your news every day

The workflow:
1. Fetches all favorited bookmarks from Karakeep
2. Extracts and analyzes tags to determine current interests (weighted by frequency)
3. Gets articles added since last run using `after:{last_run_time}` (note: `createdAt:>` is NOT supported by Karakeep CLI — use `after:` instead)
4. Scores articles based on tag matches with favorited bookmarks (substring/word overlap with frequency weighting)
5. Generates dashboard preview links for top N articles (default: 10)
6. Outputs title, summary, and link for each selected article with Telegram-friendly styling
7. Updates last run time for next execution

- Karakeep account with API access
- Karakeep CLI installed (`npm install -g @karakeep/cli`)
- Python 3.6+ for the discovery script
- Internet access for article search and feed monitoring

### Setup: Install the Discovery Script

The cron job runs scripts from `~/.hermes/scripts/`. Since the canonical `paperboy.py` lives in the skill directory, create a bash wrapper there:

```bash
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/paperboy.sh << 'EOF'
#!/bin/bash
exec python3 ~/.hermes/skills/research/paperboy/scripts/paperboy.py
EOF
chmod +x ~/.hermes/scripts/paperboy.sh
```

Then set the cron job's script to `paperboy.sh`. Do **not** symlink or copy `paperboy.py` — see Known Issues for why.

### Configure Authentication

Set up your Karakeep credentials:

```bash
# Option 1: Environment variables (recommended)
export KARAKEEP_API_KEY="your-api-key-here"
export KARAKEEP_SERVER_ADDR="https://your.karakeep.instance"
# The script also checks for KARAKEEP_URL as a fallback

# Option 2: Test your configuration
karakeep --server-addr $KARAKEEP_SERVER_ADDR --json whoami
# or
npx karakeep --server-addr $KARAKEEP_SERVER_ADDR --json whoami
```

### Schedule the Cron Job

The workflow includes a pre-configured cron job named "paperboy" that runs daily at 7:00 AM and delivers with the title "🏃💨 Paperboy Run! 🗞️":

```bash
# To view the job
hermes cron view paperboy

# To enable/disable
hermes cron pause paperboy
hermes cron resume paperboy
```

## How It Works

The workflow is now simplified to focus on discovering recent articles and generating preview URLs with user-preferred formatting:

### Phase 1: Discovery Process (Python script)

The script handles the complete workflow with robust error handling:
1. Fetches favorited bookmarks from Karakeep to determine interest tags
2. Gets articles added since last run using date-based search
3. Scores articles based on tag relevance from favorited bookmarks (with proper None-value handling)
4. Generates dashboard preview URLs for top N articles (default: 10)
5. Updates last run time for next execution
6. Outputs formatted title, summary, and link for each article with user-specified styling

### Improved Robustness (v2.0.1)

Following session 2026-05-21, the script includes enhanced error handling:
- Validates article objects before processing to prevent None-type errors
- Handles missing titles and other optional fields gracefully
- Filters invalid bookmarks from search results
- Provides detailed error logging for debugging
- Ensures workflow completion even with partial data issues
- Formats output per user preference: main title as H1 (`# `), article titles as H2 (`## `) without "Title:" prefix, with exactly one blank line between articles

### Discovery Strategy

#### 1. Interest Analysis
- Fetches all favorited bookmarks from Karakeep
- Extracts and counts tags to determine your current interests
- Excludes generic tags like "inbox"
- Uses the top tags as interest indicators

#### 2. Recent Article Detection
- Uses date-based search (`after:{last_run_time}`) to find new articles (note: `createdAt:>` is NOT supported by Karakeep CLI — use `after:` instead)
- Falls back to unfiltered search with client-side filtering if `after:` returns nothing
- Also validates article dates client-side as a safety net
- Limits results to prevent overwhelming processing
- **No longer tracks seen articles** - relies on date-based filtering

#### 3. Intelligent Selection & Scoring
- Scores articles based on tag relevance to your favorited bookmarks
- Uses tag frequency weighting: tags that appear more often in your favorited bookmarks have higher weight
- Matches tags via substring matching and word overlap for multi-word tags
- Selects only the top N articles (default: 10) for preview URL generation

#### 4. Preview URL Generation
- Generates dashboard preview URLs in the format: `https://karakeep.dex-lips.duckdns.org/dashboard/preview/<bookmark_id>`
- No tags are added per user request
- Outputs title, summary, and link for each article
- The preview URL serves as the primary means of notification



## Backlog (Not Yet Implemented)

- **Freshness decay**: Articles scored the same regardless of age within the window. Newer articles should score higher.
- **Content-type signals**: Articles with summaries could rank higher than those without.
- **Source quality weighting**: Some feeds are more relevant than others — could weight by source.

## Session References

- `references/cron-script-path-fix-2026-05-21.md` — Cron job failed because script wasn't on disk at `~/.hermes/scripts/`; also covers `deliver` target fix
- `references/cron-symlink-pitfall-2026-05-21.md` — Cron runner doesn't follow symlinks for `.py` scripts; bash wrapper is the fix
- `references/cron-agent-driven-fix-2026-05-21.md` — Cron delivery requires agent-driven jobs for chat targets like `telegram:Dane`
- `references/python3-addition-2026-05-21.md` — How to add python3 to the Hermes container via dotfiles PR

## Article Processing Pipeline

For each discovered article:
1. **Recent Check**: Verifies article was added since last run
2. **Scoring**: Calculates relevance score based on tag matches
3. **Selection**: Selects top N articles by score
4. **Preview URL Generation**: Creates dashboard preview URL for each selected article
5. **Tracking**: Updates last run time and outputs results