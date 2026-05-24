# 🗞️🏃💨 Paperboy

Automated article discovery from [Karakeep](https://github.com/karakeep-app/karakeep) favorites — interest analysis, scoring, and daily delivery with a radio-style audio briefing.

The `karakeep/` folder contains the Karakeep Hermes Agent skill (imported from [OpenClaw](https://github.com/karakeep-app/karakeep)) and is a dependency for Paperboy. See `karakeep/references/api-endpoints.md` for the full REST API reference.

## Installation

### Quick Setup

Clone the repo and run the setup script for what you need:

```bash
git clone https://github.com/dlip-hermes/paperboy.git ~/paperboy
cd ~/paperboy
```

### Paperboy (daily article discovery + radio briefing)

```bash
bash paperboy/setup-cron.sh --deliver origin
```

This installs both skills, creates the bash wrapper, state directory, and both cron jobs:

| Time | Job | What it does |
|------|-----|-------------|
| 7:00 AM | `paperboy` | Discovers articles, delivers raw list to Telegram |
| 7:05 AM | `paperboy-briefing` | Radio briefing + TTS audio agent run |

### Visual schedule

```
 7:00 AM ─ paperboy           🗞️  Raw article list delivered
 7:05 AM ─ paperboy-briefing  📻  Radio briefing + TTS audio
 8:00 AM ─ recycling-cleanup  ♻️  Recycling list emptied
```

### Keeping it tidy (Recycling)

RSS feeds can pile up fast. The **Recycling smart list** pattern keeps your dashboard focused on fresh content while preserving articles long enough for Paperboy to review them:

1. **Create a "Recycling" smart list** in the Karakeep UI with a search query that captures old RSS articles you haven't favorited:

   ```
   age:>1d source:rss -is:fav
   ```

   Bookmarks matching this query appear in the Recycling list. Once they're favorited (by you or Paperboy), they automatically leave the list.

2. **The cleanup script runs daily at 8 AM** — it deletes ALL bookmarks currently in the Recycling list using `GET /lists/{listId}/bookmarks` (the same endpoint the Karakeep UI uses). The list's query in the Karakeep UI is the single source of truth — change it to `age:>7d` and the cleanup follows.

3. **Schedule it:**

   ```bash
   bash paperboy/setup-recycling.sh --list "Recycling" --deliver origin
   ```

> **Tip:** The `age:>1d source:rss -is:fav` query is just an example. Combine any Karakeep qualifiers — `is:link`, `#tag`, `after:2026-01-01`, `age:>7d` — to build your ideal curation flow.

### Manual setup

```bash
# Copy skill folders
cp -r paperboy ~/.hermes/skills/research/
cp -r karakeep ~/.hermes/skills/research/

# Create bash wrappers (NixOS: cron runner needs .sh scripts)
mkdir -p ~/.hermes/scripts

# Paperboy discovery
cat > ~/.hermes/scripts/paperboy.sh << 'EOF'
#!/bin/bash
export PAPERBOY_MAX_ARTICLES=50
export PAPERBOY_TOP_TAGS_LIMIT=20
exec /path/to/python3 ~/.hermes/skills/research/paperboy/scripts/paperboy.py
EOF
chmod +x ~/.hermes/scripts/paperboy.sh

# Recycling cleanup
cat > ~/.hermes/scripts/cleanup-recycling.sh << 'EOF'
#!/bin/bash
exec /path/to/python3 ~/.hermes/skills/research/paperboy/scripts/cleanup-recycling.py
EOF
chmod +x ~/.hermes/scripts/cleanup-recycling.sh

# Create state directory
mkdir -p ~/.hermes/.paperboy

# Cron jobs
hermes cron create \
  --name paperboy \
  --script paperboy.sh \
  --schedule "0 7 * * *" \
  --deliver origin \
  --no-agent

hermes cron create \
  --name paperboy-briefing \
  --schedule "5 7 * * *" \
  --deliver origin \
  --skills paperboy \
  --prompt "The paperboy cron job ran at 7 AM. Review the context injected above. If it says 'Sorry mate' — forward verbatim, stop. Otherwise compose a radio briefing, generate TTS, send transcript then audio."

hermes cron create \
  --name recycling-cleanup \
  --script cleanup-recycling.sh \
  --schedule "0 8 * * *" \
  --deliver origin \
  --no-agent
```

## What you get each morning

| Time | Job | What's delivered |
|------|-----|-----------------|
| 7:00 AM | `paperboy` | Raw article list with `##` headings, summaries, and preview URLs (`no_agent` mode — always delivers) |
| 7:05 AM | `paperboy-briefing` | Radio-style briefing transcript with embedded tappable links + TTS audio voice message (agent mode) |

### How it works

1. **7:00 AM** — `paperboy.sh` runs the discovery script, which:
   - Fetches your favorited Karakeep bookmarks to learn what interests you
   - Finds new bookmarks added since the last run
   - Scores them against your interest tags (frequency-weighted)
   - Outputs the top articles with title, summary, and preview URL

2. **7:05 AM** — `paperboy-briefing` receives the paperboy output via `context_from` and:
   - Composes a conversational radio-style news briefing
   - Uses a random celebrity persona for in-character delivery
   - Embeds each article's preview URL as a tappable link on the title
   - Sends the full transcript to Telegram
   - Generates TTS audio of the spoken portion (no URLs read aloud)
   - Sends the voice message

3. **8:00 AM** — `recycling-cleanup` empties the Recycling list so your dashboard stays clean for the next day's discovery cycle.

## Workflow

1. **Add RSS feeds to Karakeep** — Configure RSS feeds in Karakeep's settings. New articles are automatically captured as bookmarks.

   > **Tip:** Enable `INFERENCE_ENABLE_AUTO_SUMMARIZATION=true` in your Karakeep server config to auto-generate AI summaries — Paperboy uses these for richer previews.

2. **Favorite what interests you** — Star bookmarks you find interesting. Paperboy learns from your favorited tags to score future articles.

3. **Paperboy runs daily** — At 7 AM you get the raw article list, at 7:05 AM the radio briefing with audio, and at 8 AM the Recycling list is emptied.

## Features

- **Interest Analysis** — Extracts and ranks tags from your favorited bookmarks (frequency-weighted)
- **Recent Article Detection** — Finds articles bookmarked since the last run using Karakeep's `after:` date filter plus client-side validation
- **Tag-Based Scoring** — Scores articles by tag relevance with substring and word-overlap matching
- **Preview URL Generation** — Dashboard preview links for the top scored articles
- **Hybrid Cron Delivery** — Raw output guaranteed at 7 AM (`no_agent`), radio briefing + TTS at 7:05 AM (agent mode via `context_from`)
- **Recycling Cleanup** — Auto-deletes old RSS bookmarks via the Recycling smart list's own query — change the list query in the UI and the cleanup follows

## Standalone Usage

```bash
# Prerequisites
export KARAKEEP_SERVER_ADDR="https://your-karakeep-instance.example.com"
export KARAKEEP_API_KEY="your-api-key"

# Paperboy discovery
python3 paperboy/scripts/paperboy.py

# Recycling cleanup
python3 paperboy/scripts/cleanup-recycling.py
```

## Configuration

| Setting | Default | Env Var | Description |
|---------|---------|---------|-------------|
| `MAX_ARTICLES` | 50 | `PAPERBOY_MAX_ARTICLES` | Maximum articles to deliver per run |
| `TOP_TAGS_LIMIT` | 20 | `PAPERBOY_TOP_TAGS_LIMIT` | Number of interest tags to use for scoring |
| `EXCLUDED_TAGS` | `{'inbox'}` | — | Tags to ignore when ranking interests |
| State file | `~/.hermes/.paperboy/state.json` | — | Tracks last run time |

### Recycling cleanup

The cleanup is driven by the Recycling smart list's query in the Karakeep UI — no env var needed. To change what gets deleted, update the list's query (e.g., `age:>7d source:rss -is:fav`).

## License

MIT
