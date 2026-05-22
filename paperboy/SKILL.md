---
name: paperboy
description: Automated workflow to discover articles based on favorited Karakeep bookmarks and deliver them via dashboard preview links with title, summary, and link — named "🏃💨 Paperboy Run! 🗞️" because it delivers your news every day.
version: 2.2.0
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
5. **Detailed Output**: Outputs title, summary, and link for each article (when no new articles are found, outputs a friendly "Sorry mate there's no new news at the moment" message)
6. **Automation**: Runs automatically via cron job to deliver your news every day

The workflow:
1. Fetches all favorited bookmarks from Karakeep
2. Extracts and analyzes tags to determine current interests (weighted by frequency)
3. Gets articles added since last run using `after:{date_minus_1_day}` (YYYY-MM-DD only) + client-side createdAt comparison for sub-day precision
4. Scores articles based on tag matches with favorited bookmarks (substring/word overlap with frequency weighting)
5. Generates dashboard preview links for top N articles (default: 10)
6. Outputs title, summary, and link for each selected article (or friendly no-news message if nothing new)
7. Updates last run time for next execution

### Hybrid Cron Delivery (raw output + agent TTS report)

Paperboy uses a **two-job hybrid approach** for delivery, combining the reliability of `no_agent` mode with agent-driven TTS audio:

| Job | Time | Mode | Purpose | Reliable? |
|-----|------|------|---------|-----------|
| `paperboy` | 7:00 AM | `no_agent` + `script` | Runs discovery, delivers raw article list verbatim to Telegram | ✅ High |
| `paperboy-briefing` | 7:15 AM | Agent mode (no script) | Reads `paperboy.md`, composes radio briefing + TTS audio | ⚠️ Medium |

> **⚠️ Scheduler limitation:** Agent-mode cron jobs are only processed during natural scheduler ticks (every ~60 min). `cronjob run <id>` queues a job but `cronjob run` doesn't trigger immediate execution, and `hermes cron tick` doesn't process agent-mode jobs. To test the briefing flow, execute it manually — the scheduled 7:15 AM run works when the natural tick picks it up.

**How the relay works:**

1. `paperboy.sh` writes output to both stdout (for cron delivery) AND `~/.hermes/.paperboy/paperboy.md` (the shared file)
2. At 7:00 AM, `paperboy` delivers the raw output to Telegram immediately
3. At 7:15 AM, `paperboy-briefing` reads the `.paperboy/paperboy.md` file and creates a radio briefing + TTS audio

**Agent job prompt (exact text):** The agent-mode cron job has no script. Its prompt reads the shared file:

> The paperboy cron job ran at 7 AM and wrote its output to ~/.hermes/.paperboy/paperboy.md. Read that file.
> 
> If the file contains "Sorry mate there's no new news at the moment", just forward that message verbatim via send_message() (no audio needed). STOP after that.
> 
> Otherwise: (1) Compose a radio-style news briefing. For each article, embed its preview URL as a markdown link on the title text (e.g. [Title](url)) followed by a short summary. (2) Send the transcript as a text message. (3) Generate TTS audio of just the spoken portion (no URLs, no markdown) using text_to_speech(). (4) Send the audio file via send_message() with MEDIA:path in the message text.

**Context chaining (optional):** Set `context_from` on the agent job to the raw job's ID — this injects the raw output as fallback context if the file read fails.

**Output paths:**
- **No articles found**: Raw job delivers "Sorry mate..." → Briefing job sees same message, forwards verbatim. No audio.
- **Articles found**: Raw job delivers article list → Briefing job composes radio briefing + TTS voice message.

> **ℹ️ `deliver: origin` vs `send_message()`:** Cron's `deliver: origin` auto-detects the current chat and works correctly. But `send_message(target="origin")` returns "Unknown platform: origin" — it requires an explicit target like `"telegram:Dane"`. Agent prompts should use explicit target names or rely on cron delivery.

> **Note on raw output integrity:** The `paperboy` job runs in `no_agent` mode — the cron runner delivers its stdout verbatim with no opportunity for the agent to reformat. The `paperboy-briefing` job reads the file but only produces the radio briefing + TTS audio; it never re-outputs the raw article list. This split guarantees raw output fidelity without guardrails.

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
# Paperboy launcher — delegates to the skill-owned Python script
# Writes to .paperboy/paperboy.md for follow-up agent job to pick up
exec /var/lib/hermes/.nix-profile/bin/python3 \
  ~/.hermes/skills/research/paperboy/scripts/paperboy.py \
  --output-file ~/.hermes/.paperboy/paperboy.md
EOF
chmod +x ~/.hermes/scripts/paperboy.sh
```

The `--output-file` argument writes the same output to `~/.hermes/.paperboy/paperboy.md` for the downstream agent-mode cron job to read. The wrapper script also handles the absolute path to Python in the NixOS container.

Then set the cron job's script to `paperboy.sh`. Do **not** symlink or copy `paperboy.py` — the Hermes cron runner doesn't follow symlinks for `.py` scripts (fails silently), and copies drift from the skill's version.

> **Recommended:** Set `INFERENCE_ENABLE_AUTO_SUMMARIZATION=true` in your Karakeep server environment. Paperboy uses article summaries in its preview output — auto-generated AI summaries produce richer, more useful previews than raw excerpts.

### Configure Authentication

Set up your Karakeep credentials:

```bash
# Option 1: Environment variables (recommended)
export KARAKEEP_API_KEY="your-api-key-here"
export KARAKEEP_SERVER_ADDR="https://your.karakeep.instance"
# The script also checks for KARAKEEP_URL as a fallback

# Option 2: Test your configuration
npx karakeep --server-addr $KARAKEEP_SERVER_ADDR --json whoami
```

### Schedule the Cron Jobs

The workflow uses **two cron jobs** for hybrid delivery:

**Job 1 — Raw discovery (reliable, no agent):**

```bash
hermes cron create \
  --name paperboy \
  --script paperboy.sh \
  --schedule "0 7 * * *" \
  --deliver origin \
  --no-agent
```

**Job 2 — Briefing (agent-mode radio + TTS, 15 min later):**

```bash
hermes cron create \
  --name paperboy-briefing \
  --schedule "15 7 * * *" \
  --deliver origin \
  --skills paperboy \
  --prompt "The paperboy cron job ran at 7 AM and wrote its output to ~/.hermes/.paperboy/paperboy.md. Read that file. If the file contains 'Sorry mate' — forward verbatim via send_message() (no audio needed). STOP after that. Otherwise: (1) Compose a radio-style news briefing. For each article, embed its preview URL as a markdown link on the title text (e.g. [Title](url)) followed by a short summary. (2) Send the transcript as a text message. (3) Generate TTS audio of just the spoken portion (no URLs, no markdown) using text_to_speech(). (4) Send the audio file via send_message() with MEDIA:path in the message text."
```

To chain the agent job to the raw job's output as fallback context (injects raw job's stdout into agent session):

```bash
# First get the raw job's ID
hermes cron list
# Then set context_from to chain them
hermes cron update <paperboy-briefing-id> --context-from <paperboy-id>
```

## How It Works

The workflow is now simplified to focus on discovering recent articles and generating preview URLs with user-preferred formatting:

#### Phase 1: Discovery Process (Python script)

The script handles the complete workflow with robust error handling:
1. Fetches favorited bookmarks from Karakeep to determine interest tags
2. Gets articles added since last run using date-based search (YYYY-MM-DD minus 1 day query + client-side createdAt dedup)
3. Scores articles based on tag relevance from favorited bookmarks
4. Generates dashboard preview URLs for top N articles (default: 10)
5. Updates last run time for next execution
6. Outputs formatted title, summary, and link to stdout AND (if `--output-file` is passed) to a shared file for downstream jobs
7. If no new articles, prints heading + "Sorry mate there's no new news at the moment"

### Improved Robustness (v2.0.1)

Following session 2026-05-21, the script includes enhanced error handling:
- Validates article objects before processing to prevent None-type errors
- Handles missing titles and other optional fields gracefully
- Filters invalid bookmarks from search results
- Provides detailed error logging for debugging
- Ensures workflow completion even with partial data issues

### Discovery Strategy

#### 1. Interest Analysis
- Fetches all favorited bookmarks from Karakeep
- Extracts and counts tags to determine your current interests
- Excludes generic tags like "inbox"
- Uses the top tags as interest indicators
### Recent Article Detection & Date Filtering

The workflow uses a two-layer approach to handle Karakeep's `after:` filter limitation (only accepts `YYYY-MM-DD`, not full timestamps):

1. **Query layer**: Requests `after:{date_minus_1_day}` (e.g., `after:2026-05-21` for a last run on 2026-05-22) — this gives a safe window so nothing is missed
2. **Client-side filter**: Compares each bookmark's `createdAt` field (UTC ISO string) against the precise last-run timestamp for exact dedup

**Default window:** When no state file exists (first run or after clearing), the default window is **48 hours** instead of 24 hours. This wider window ensures articles aren't missed if there's a timezone or scheduling gap.

This guarantees no articles are missed from a timezone boundary or sub-day precision gap. The `after:` filter is purely a server-side optimization to reduce the result set; correctness depends on the client-side timestamp comparison.

#### 3. Intelligent Selection & Scoring
- Scores articles based on tag relevance to your favorited bookmarks
- Uses tag frequency weighting: tags that appear more often in your favorited bookmarks have higher weight
- Matches tags via substring matching and word overlap for multi-word tags
- Selects only the top N articles (default: 10) for preview URL generation

> **⚠️ CRITICAL PITFALL — `output_lines = []` must exist before any `append()` call:** The buffer-based refactor (v2.2.0) collects output in `output_lines = []`. The no-news return path (`return 0`) is BEFORE the `# Score articles` section. If `output_lines` is accidentally moved below the early-return path, `output_lines.append()` on the no-news path will raise `AttributeError`. Always verify the `output_lines = []` line is at the top of `main()`, before all `append()` calls. Similarly, `scored_articles = []` must exist before the `# Score articles` section. The cron scheduler's `script` field pre-runs the script before the agent session; if the prompt says "Run the script..." the agent will re-run it and get stale results — always phrase as "The script has already run..."

#### 4. Preview URL Generation
- Generates dashboard preview URLs in the format: `https://karakeep.dex-lips.duckdns.org/dashboard/preview/<bookmark_id>`
- No tags are added per user request
- Outputs title, summary, and link for each article
- The preview URL serves as the primary means of notification



## State Files

The workflow stores persistent state in `~/.hermes/.paperboy/`:

| File | Purpose |
|------|---------|
| `paperboy.md` | Output from the latest Paperboy run; read by the agent cron job for radio report + TTS |
| `state.json` | Tracks last run timestamp to filter out already-processed articles |
| `seen_articles.json` | (Deprecated, kept for migration) Previously tracked seen article IDs |
| `learned_tags.json` | Learned tag effectiveness data collected across runs |
| `summary_cache.json` | Cached article summaries to avoid redundant API calls |

The directory was renamed from `.article_discovery` to `.paperboy` in May 2026 to match the workflow name.

## Backlog (Not Yet Implemented)

- **Freshness decay**: Articles scored the same regardless of age within the window. Newer articles should score higher.
- **Content-type signals**: Articles with summaries could rank higher than those without.
- **Source quality weighting**: Some feeds are more relevant than others — could weight by source.

## Companion Workflows

### Recycling list auto-cleanup

Set up a "Recycling" smart list that auto-catches unwanted RSS articles, then schedule a daily purge at 8 AM (after Paperboy runs):

```
source:rss -is:fav
```

The `cleanup-recycling.py` script finds all bookmarks in the Recycling list and deletes them. See `references/recycling-cleanup-pattern.md` for setup details.

Key benefits:
- Runs at 8 AM, after Paperboy has already discovered and delivered articles (7:00-7:15)
- `no_agent` cron mode — always reliable, no agent overhead
- Silent on empty list — no noise when there's nothing to clean

## Session References

- `references/paperboy-briefing-refinements-2026-05-22.md` — Briefing refinements: removed raw output from briefing, embedded links as markdown, cron rename sequence, scheduler unreliability confirmed
- `references/file-relay-cron-chaining.md` — File-based relay between `no_agent` and agent cron jobs; `--output-file` pattern, context chaining, pitfalls
- `references/agent-tts-news-report-setup-2026-05-22.md` — TTS news report agent delivery setup; cron prompt, two output paths (no articles → plain text, articles → TTS voice + text)
- `references/cron-scheduler-unreliability-2026-05-22.md` — Cron scheduler delivery bugs: `cronjob run` not executing, `cron tick` timing out, agent re-running scripts, and delivery workarounds
- `references/date-filter-YYYY-MM-DD-only-2026-05-22.md` — `after:` only accepts `YYYY-MM-DD`; fix uses date-minus-1-day query + client-side timestamp filter
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