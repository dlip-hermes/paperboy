# 🗞️🏃💨 Paperboy

Automated article discovery from [Karakeep](https://github.com/karakeep-app/karakeep) favorites — interest analysis, scoring, and daily delivery with a radio-style audio briefing.

The `karakeep/` folder contains the Karakeep Hermes Agent skill (imported from [OpenClaw](https://github.com/karakeep-app/karakeep)) and is a dependency for Paperboy.

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
| 7:15 AM | `paperboy-briefing` | Radio briefing + TTS audio with embedded links |

### Visual schedule

```
 7:00 AM ─ paperboy           🗞️  Raw article list delivered
 7:15 AM ─ paperboy-briefing  📻  Radio briefing + TTS audio
 8:00 AM ─ recycling-cleanup  ♻️  Recycling bin emptied
```

### Keeping it tidy

RSS feeds can pile up quickly. The **Recycling smart list** pattern keeps your dashboard focused on fresh content:

1. **Create a "Recycling" smart list** — Use a search query that captures RSS articles older than 3 days that you haven't favorited:

   ```
   age:>3d source:rss -is:fav
   ```

2. **Auto-delete daily at 8 AM** — Run the setup script to schedule a daily purge:

   ```bash
   bash paperboy/setup-recycling.sh --list "Recycling" --deliver origin
   ```

   This deletes all bookmarks in the Recycling list every morning after Paperboy has delivered your briefing. The cleanup script loops until the list is empty, so it handles feeds that keep pushing items during deletion.

3. **Or archive instead of delete** — If you'd rather keep them searchable, run this via the Karakeep CLI:

   ```bash
   karakeep bookmarks search "list:Recycling" --limit 50 --json | \
     jq -r '.bookmarks[].id' | xargs -I{} karakeep bookmarks update {} --archive
   ```

Paperboy still searches archived bookmarks for interest analysis, so archiving doesn't affect your tag learning.

> **Tip:** The `age:>3d source:rss -is:fav` query is just an example. Combine any Karakeep qualifiers — `is:link`, `#tag`, `after:2026-01-01` — to build your ideal curation flow.

### Manual setup

```bash
# Copy skill folders
cp -r paperboy ~/.hermes/skills/research/
cp -r karakeep ~/.hermes/skills/research/

# Create bash wrapper
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/paperboy.sh << 'EOF'
#!/bin/bash
exec python3 ~/.hermes/skills/research/paperboy/scripts/paperboy.py \
  --output-file ~/.hermes/.paperboy/paperboy.md
EOF
chmod +x ~/.hermes/scripts/paperboy.sh

# Create state directory
mkdir -p ~/.hermes/.paperboy

# Cron job 1 — raw delivery (reliable)
hermes cron create \
  --name paperboy \
  --script paperboy.sh \
  --schedule "0 7 * * *" \
  --deliver origin \
  --no-agent

# Cron job 2 — radio briefing + TTS (15 min later)
hermes cron create \
  --name paperboy-briefing \
  --schedule "15 7 * * *" \
  --deliver origin \
  --skills paperboy \
  --prompt "The paperboy cron job ran at 7 AM and wrote its output to ~/.hermes/.paperboy/paperboy.md. Read that file. If the file contains 'Sorry mate' — forward verbatim, stop. Otherwise compose a radio briefing with embedded links, generate TTS, send transcript then audio."

# Chain context for fallback
hermes cron update <paperboy-briefing-id> --context-from <paperboy-id>
```

## What you get each morning

| Time | Job | What's delivered |
|------|-----|-----------------|
| 7:00 AM | `paperboy` | Raw article list with `##` headings, summaries, and preview URLs (no_agent mode — always delivers) |
| 7:15 AM | `paperboy-briefing` | Radio-style briefing transcript with [embedded tappable links](url) + TTS audio voice message (agent mode) |

### How it works

1. **7:00 AM** — `paperboy.sh` runs the discovery script, which:
   - Fetches your favorited Karakeep bookmarks to learn what interests you
   - Finds new bookmarks added since the last run
   - Scores them against your interest tags (frequency-weighted)
   - Outputs the top 10 with title, summary, and preview URL
   - Writes the same output to `~/.hermes/.paperboy/paperboy.md` for the briefing job

2. **7:15 AM** — `paperboy-briefing` reads `paperboy.md` and:
   - Composes a conversational radio-style news briefing
   - Embeds each article's preview URL as a tappable link on the title
   - Sends the full transcript to Telegram
   - Generates TTS audio of the spoken portion (no URLs read aloud)
   - Sends the voice message

## Workflow

1. **Add RSS feeds to Karakeep** — Configure RSS feeds in Karakeep's settings. New articles are automatically captured as bookmarks.

   > **Tip:** Enable `INFERENCE_ENABLE_AUTO_SUMMARIZATION=true` in your Karakeep server config to auto-generate AI summaries — Paperboy uses these for richer previews.

2. **Favorite what interests you** — Star bookmarks you find interesting. Paperboy learns from your favorited tags to score future articles.

3. **Paperboy runs daily** — At 7 AM you get the raw article list, at 7:15 AM the radio briefing with audio.

## Features

- **Interest Analysis** — Extracts and ranks tags from your favorited bookmarks (frequency-weighted)
- **Recent Article Detection** — Finds articles bookmarked since the last run using Karakeep's `after:` date filter plus client-side validation
- **Tag-Based Scoring** — Scores articles by tag relevance with substring and word-overlap matching
- **Preview URL Generation** — Dashboard preview links for the top N scored articles (default: 10)
- **Hybrid Cron Delivery** — Raw output guaranteed at 7 AM, radio briefing + TTS at 7:15 AM
- **`--output-file` Support** — Writes output to a shared file so the agent-mode job can pick it up without re-running the discovery script

## Standalone Usage

```bash
# Prerequisites
export KARAKEEP_SERVER_ADDR="https://your-karakeep-instance.example.com"
export KARAKEEP_API_KEY="your-api-key"

# Run (stdout + file output)
python3 paperboy/paperboy.py --output-file ~/.paperboy/output.md

# Or just stdout
python3 paperboy/paperboy.py
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ARTICLES` | 10 | Maximum articles to deliver per run |
| `TOP_TAGS_LIMIT` | 8 | Number of interest tags to use for scoring |
| `EXCLUDED_TAGS` | `{'inbox'}` | Tags to ignore when ranking interests |
| State file | `~/.hermes/.paperboy/state.json` | Tracks last run time |

## License

MIT
