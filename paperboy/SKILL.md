---
name: paperboy
description: Automated workflow to discover articles based on favorited Karakeep bookmarks and deliver them via dashboard preview links with title, summary, and link — named "🏃💨 Paperboy Run! 🗞️" because it delivers your news every day.
version: 2.6.0
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
| `paperboy-briefing` | 7:05 AM | Agent mode (no script) | Reads injected context from paperboy job, composes radio briefing + TTS audio | ⚠️ Medium (queued, runs at next tick) |

> **⚠️ TTS generation may be skipped by the agent model:** The briefing agent's `text_to_speech()` step is not always reliably executed — the model may compose and send the text briefing but fail to generate audio. This happened on 2026-05-23 with nvidia/nemotron-3-super-120b-a12b:free. TTS itself works (edge provider is functional). To improve reliability: pin the briefing job to a specific model via cron's `model` field, or add a verification instruction to the prompt ("After generating TTS, confirm the file exists before sending"). **Proven working:** `deepseek/deepseek-v4-flash` via OpenRouter successfully generated TTS at the 10:45 natural tick on 2026-05-23. See `references/tts-reliability-2026-05-23.md` for full investigation.

> **⚠️ Scheduler limitation — natural tick clarification:** Agent-mode cron jobs are **only processed during natural scheduler ticks** (when any `no_agent` job fires on schedule). With the 5-minute tick-pacer in place, the maximum wait is now **5 minutes** instead of the previous 60 minutes (auto-backup cycle). `cronjob run <id>` queues a job but doesn't trigger immediate execution. To test the briefing flow immediately, execute it manually from an active session. See `references/tick-pacer-pattern.md` for setup.

**How the relay works:**

1. `paperboy.sh` runs and outputs article data to stdout
2. Hermes cron captures stdout and delivers it to Telegram (raw output) at 7:00 AM
3. Hermes cron also injects the same stdout into the briefing job's context via `context_from`
4. At 7:05 AM, the briefing agent reads the injected context and creates a radio briefing + TTS audio

No file relay is needed. The `--output-file` flag is not used — stdout is the single source of truth for both the raw delivery and the briefing context.

**Agent job prompt (current version):** The agent-mode cron job has no script. Its prompt reads the injected context:

> If the article data says "Sorry mate there's no new news at the moment", just forward that message verbatim via send_message() (no audio needed). STOP after that.
>
> Otherwise, pick a random celebrity persona (could be anyone — Samuel L. Jackson, Gordon Ramsay, Gollum, RuPaul, Borat, Fran Fine, Yoda, whomever). Introduce yourself as that celebrity at the start, then deliver a radio-style news briefing in that character's voice.
>
> Group articles by general topic (e.g. "Tech & AI", "Space", "Legal", "Deals & Sales", "Security", "Culture"). Introduce each topic section with a short headline, then cover the articles under it.
>
> Each article has a Score value. Spend more time on higher-scoring articles — write a fuller explanation (3-4 sentences) for the top scorers. For lower-scoring articles, still include at least 1 sentence of real summary.
>
> CRITICAL — For EACH article, you MUST include:
> 1. The title as a tappable markdown link: [Title](preview URL)
> 2. At LEAST 1 sentence of actual summary (3-4 sentences for top-scoring articles).
> 3. Then optionally a short character joke/flourish on top.
>
> The summaries are the real informative content — don't skip them. Each article should feel substantive, not just a punchline delivery vehicle.
>
>(1) Compose the full briefing transcript with character intro + embedded links + summaries and send it as a text message via send_message().
>(2) Generate TTS audio of just the spoken portion (no URLs, no markdown, but DO include the character intro and the real article summaries) using text_to_speech() — keep the character voice in the audio too. Articles with Score: 0 have no summary text in the output, so the TTS naturally reads only their titles.
>(3) Send the audio file via send_message() with MEDIA:path in the message text.

> **Prompt evolution:** The briefing prompt has evolved through several stages:
> 1. **Generic radio briefing** — original design
> 2. **Ricky Gervais cynical style** — user preferred personality-driven delivery
> 3. **Random celebrity persona** — variety with character intro at start
> 4. **Summary requirement added** — user's critical feedback: "very little article summary — just a heading and a joke" prompt updated to require **at least 2 sentences of real summary** before character flourishes. Core lesson: summaries are the meal, character voice is the topping.
> 5. **Topic grouping** — articles grouped by general category (Tech & AI, Space, Legal, etc.) with section headlines
> 6. **Score-based depth** — scores added to raw output; briefing spends 3-4 sentences on top scorers, 1+ on rest
> 7. **Clean prompt** — data sourcing instructions removed entirely; Hermes' `context_from` auto-injects the data and tells the agent where to find it. The prompt only says *what to do* with the data.
> 8. **Source-level Score: 0 handling** — `paperboy.py` omits summary text for Score: 0 articles. Since no summary exists in the output, the TTS naturally reads only the titles without any special prompt instruction. Score > 0 articles are read in full. The embedded link format (`## [Title](url)`) means titles are tappable in Telegram without a separate URL line.

### Context Chaining via `context_from`

The `paperboy-briefing` cron job has `context_from` set to the `paperboy` job ID. Hermes cron automatically captures stdout from the raw job and injects it as context into the briefing job's prompt. This means:

- **No file relay needed** — the paperboy script no longer writes to a shared file
- **No `--output-file` flag** — stdout is captured and delivered by cron directly
- **Reliable data flow** — the briefing agent always sees the raw article output in its context
- **Dual-path delivery** — the raw stdout is also delivered to Telegram via the no_agent cron, so you get both the raw list and the polished briefing

**How to set it up:**
```bash
# Get the raw job's ID
hermes cron list
# Then set context_from to chain them (use cronjob tool, not CLI — `hermes cron edit` has no --context-from flag)
# In an agent session: cronjob action="update" job_id="<briefing-id>" context_from="<raw-id>"
# Or via the hermes-agent skill's documented cronjob tool
```

**Output paths:**
- **No articles found**: Raw job delivers "Sorry mate..." → Briefing job sees same message, forwards verbatim. No audio.
- **Articles found**: Raw job delivers article list → Briefing job composes radio briefing + TTS voice message.

> **⚠️ `deliver: origin` only works for agent-mode cron jobs:** Cron's `deliver: origin` auto-detects the current chat in **agent-mode** jobs. For **no_agent mode** script jobs, `deliver: origin` fails with `"no delivery target resolved for deliver=origin"` — you must set an explicit target like `"telegram:Dane"`. See `references/deliver-origin-noagent-fix-2026-05-23.md` for details.
> 
> Also, `send_message(target="origin")` returns "Unknown platform: origin" — it requires an explicit target like `"telegram:Dane"`. Agent prompts should use explicit target names or rely on cron delivery.

> **Note on raw output integrity:** The `paperboy` job runs in `no_agent` mode — the cron runner delivers its stdout verbatim with no opportunity for the agent to reformat. The `paperboy-briefing` job receives the same stdout via `context_from` and produces the radio briefing + TTS audio; it never re-outputs the raw article list. This split guarantees raw output fidelity without guardrails.

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
# Output is captured by Hermes cron and injected into briefing via context_from
export PAPERBOY_MAX_ARTICLES=50
exec /var/lib/hermes/.nix-profile/bin/python3 \
  ~/.hermes/skills/research/paperboy/scripts/paperboy.py
EOF
chmod +x ~/.hermes/scripts/paperboy.sh
```

The wrapper script handles the absolute path to Python in the NixOS container. No `--output-file` flag is used — Hermes cron captures stdout and injects it into the briefing job via `context_from`.

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
  --deliver "telegram:Dane" \
  --no-agent
```

> **Note:** Use an explicit `--deliver "telegram:Dane"` target (your actual Telegram handle). `--deliver origin` does NOT resolve in `no_agent` mode — see the warning above.

**Job 2 — Briefing (agent-mode radio + TTS, 5 minutes later):**

```bash
hermes cron create \
  --name paperboy-briefing \
  --schedule "5 7 * * *" \
  --deliver "telegram:Dane" \
  --skills paperboy \
  --model '{"provider": "opencode-go", "model": "deepseek-v4-pro"}' \
  --prompt "If the article data says \"Sorry mate there's no new news at the moment\", just forward that message verbatim via send_message() (no audio needed). STOP after that. Otherwise, pick a random celebrity persona and deliver a radio-style news briefing. Group articles by general topic (e.g. \"Tech & AI\", \"Space\", \"Legal\", \"Deals & Sales\", \"Security\", \"Culture\"), introducing each section with a short headline. For each article, embed its preview URL as a markdown link on the title and include the appropriate level of summary. Generate TTS audio and send the audio file after the transcript."
```

Then chain the jobs together via `context_from` (this replaces the old file-relay pattern):

```bash
# Get job IDs
RAW_ID=$(hermes cron list | grep -B1 '"name": "paperboy"' | grep job_id | sed 's/.*"\([^"]*\)".*/\1/')
BRIEFING_ID=$(hermes cron list | grep -B1 '"name": "paperboy-briefing"' | grep job_id | sed 's/.*"\([^"]*\)".*/\1/')
# Chain them — briefing receives paperboy's stdout as context
hermes cron update "$BRIEFING_ID" --context-from "$RAW_ID"
```

The `context_from` mechanism captures stdout from the raw job and injects it into the briefing job's prompt. This eliminates the need for a shared file — the briefing agent reads the article data directly from its injected context. See the [Context Chaining](#context-chaining-via-context_from) section for details.

> **💡 Per-job model overrides:** Agent-mode cron jobs support an optional `model` field to pin a specific model/provider. This is useful when a particular model handles multi-step prompts (text briefing + TTS audio) more reliably. **Set via the `cronjob` tool, NOT the CLI** — the CLI's `hermes cron edit` has no `--model` flag. Use `cronjob action="update"` with `model='{"provider":"<provider>", "model":"<model-id>"}'`. Omit `provider` to keep the system default provider.
>
> **Removing a model override:** There is no explicit "clear" operation — passing empty objects (`{}`, `[]`, `{"model":"","provider":""}`, or `null` values) all fail with `"No updates provided."`. To functionally remove a custom model override, set the model to match the current system default (check with `hermes config get model.default`). The job will then track whatever the system default is, which is equivalent to having no override. See `references/cron-model-management.md` for full details.

## How It Works

The workflow is now simplified to focus on discovering recent articles and generating preview URLs with user-preferred formatting:

#### Phase 1: Discovery Process (Python script)

The script handles the complete workflow with robust error handling:
1. Fetches favorited bookmarks from Karakeep to determine interest tags
2. Gets articles added since last run using date-based search (YYYY-MM-DD minus 1 day query + client-side createdAt dedup)
3. Scores articles based on tag relevance from favorited bookmarks
4. Generates dashboard preview URLs for top N articles (default: 10)
5. Updates last run time for next execution
6. Outputs formatted title, summary, and link to stdout (captured by Hermes cron and delivered to Telegram + injected into briefing job via `context_from`)
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
### Design Principle: No Filtering

Articles are **never filtered out** before scoring. All discovered bookmarks pass through to the scoring engine regardless of whether they have tags, AI summaries, descriptions, or any other metadata. The scoring algorithm does its work based on whatever data is available (tag matches, title keyword matches), and the top N highest-scored articles are delivered (configurable via `PAPERBOY_MAX_ARTICLES` env var). If a bookmark has no tags, it scores based on title keyword overlap only.

> This was an explicit choice: earlier versions attempted to filter out articles without AI summaries (summary filter) or without tags (tag filter), but both were dropped because fresh RSS captures often arrive without either, and the user prefers seeing everything scored rather than risk missing content.

### Recent Article Detection & Date Filtering

The workflow uses a two-layer approach to handle Karakeep's `after:` filter limitation (only accepts `YYYY-MM-DD`, not full timestamps):

1. **Query layer**: Requests `after:{date_minus_1_day}` (e.g., `after:2026-05-21` for a last run on 2026-05-22) — this gives a safe window so nothing is missed
2. **Client-side filter**: Compares each bookmark's `createdAt` field (UTC ISO string) against the precise last-run timestamp for exact dedup

**Default window:** When no state file exists (first run or after clearing with `echo '{}'`), the default window is **24 hours**. This matches the expected behavior of finding only recent articles.

This guarantees no articles are missed from a timezone boundary or sub-day precision gap. The `after:` filter is purely a server-side optimization to reduce the result set; correctness depends on the client-side timestamp comparison.

#### 3. Intelligent Selection & Scoring
- Scores articles based on tag relevance to your favorited bookmarks
- Uses tag frequency weighting: tags that appear more often in your favorited bookmarks have higher weight
- Matches tags via substring matching and word overlap for multi-word tags
- **⚠️ Tag format**: Karakeep tags are dicts (`{"id":..., "name":..., "attachedBy":...}`), not strings. `extract_tags_from_bookmarks()` and `score_article()` must extract `tag["name"]` before matching. Failing to do so causes every article to score 0 (calling `.lower()` on a dict raises AttributeError silently). Fixed in v2.5.0.
- Selects only the top N articles (configurable via `PAPERBOY_MAX_ARTICLES` env var, default 10) for preview URL generation, scored against the top M interest tags (configurable via `PAPERBOY_TOP_TAGS_LIMIT` env var, default 8)

> **⚙️ Cron-override pattern — never change script defaults for deployment config:** If the user wants a different value for MAX_ARTICLES, TOP_TAGS_LIMIT, or other config, do NOT change the constant in the script. Instead: (1) Make the script read an env var with a sensible default, then (2) export that env var ONLY in the active cron wrapper (`~/.hermes/scripts/paperboy.sh`). The `setup-cron.sh` template generates a fresh-install wrapper with defaults for new users — your live wrapper is the authoritative deployment layer. Keep the script usable standalone; config belongs in the wrapper.

> **📋 Env var reference:**
> | Env Var | Default | Used by | Description |
> |---------|---------|---------|-------------|
> | `PAPERBOY_MAX_ARTICLES` | `10` | `paperboy.py` | Maximum articles to deliver per run. Set to `-1` for no limit. |
> | `PAPERBOY_TOP_TAGS_LIMIT` | `-1` | `paperboy.py` | Number of interest tags to use for scoring. Default `-1` means ALL tags. |
>
> **💡 Verification:** To confirm `PAPERBOY_MAX_ARTICLES=-1` works correctly, compare output article counts between runs with different values (e.g., 10, 20, -1). The -1 setting should include all scored articles in the output.

> **⚠️ CRITICAL PITFALL — State file management during testing:** Manually running `paperboy.py` or `paperboy.sh` updates `~/.hermes/.paperboy/state.json` with the current timestamp. This causes the **next scheduled cron run to skip the same articles** because the client-side `createdAt` filter excludes anything before the manual run's timestamp. **Always reset the state file after manual testing** — use `echo '{}' > ~/.hermes/.paperboy/state.json` (forces 24-hour default window) or set a specific pre-article timestamp. See `references/state-management-testing.md` for details.

> **Quick trigger shorthand:** When the user says "trigger Paperboy" or "trigger paperboy", execute these three steps in order: (1) clear the state file with `echo '{}' > ~/.hermes/.paperboy/state.json`, (2) `cronjob run 6e02176c58a6` (paperboy discovery, runs immediately as no_agent), (3) `cronjob run 64948a9fd8e2` (paperboy-briefing, queues for next tick). Do not wait between steps — fire all three in parallel.
>
> > **⚠️ CRITICAL PITFALL — `output_lines = []` must exist before any `append()` call:** The buffer-based refactor collects output in `output_lines = []`. The no-news return path (`return 0`) is BEFORE the Score articles section. If `output_lines` is accidentally moved below the early-return path, `output_lines.append()` on the no-news path will raise `AttributeError`. Always verify `output_lines = []` is at the top of `main()`, before all `append()` calls. Similarly, `scored_articles = []` must exist before the Score articles section. The cron scheduler's `script` field pre-runs the script before the agent session; if the prompt says "Run the script..." the agent will re-run it and get stale results — always phrase as "The script has already run..."

### Output Format

Each article in the raw output has this compact structure (titles are tappable links in Telegram):

```
## [Title](https://karakeep.dex-lips.duckdns.org/dashboard/preview/abc123) (Score: 5)

Summary text here...
```

**Score: 0 articles omit the summary** — only the title line with link and score is output:

```
## [Title](https://karakeep.dex-lips.duckdns.org/dashboard/preview/abc123) (Score: 0)
```

Articles are back-to-back with no extra blank line between them. The briefing agent naturally handles Score: 0 articles as title-only reads since no summary text is present. The `Score` represents tag-relevance weighting.

#### 4. Preview URL Generation
- Generates dashboard preview URLs in the format: `https://karakeep.dex-lips.duckdns.org/dashboard/preview/<bookmark_id>`
- No tags are added per user request
- Outputs title, summary, and link for each article
- The preview URL serves as the primary means of notification



## State Files

The workflow stores persistent state in `~/.hermes/.paperboy/`:

| File | Purpose |
|------|---------|
| `paperboy.md` | (Legacy) Output from a previous Paperboy run. No longer actively written or read — the context_from relay replaces this file. |
| `state.json` | Tracks last run timestamp to filter out already-processed articles |
| `seen_articles.json` | (Deprecated, kept for migration) Previously tracked seen article IDs |
| `learned_tags.json` | Learned tag effectiveness data collected across runs |
| `summary_cache.json` | Cached article summaries to avoid redundant API calls |

The directory was renamed from `.article_discovery` to `.paperboy` in May 2026 to match the workflow name.

## Backlog (Not Yet Implemented)

- **Freshness decay**: Articles scored the same regardless of age within the window. Newer articles should score higher.
- **Source quality weighting**: Some feeds are more relevant than others — could weight by source.

## Companion Workflows

### Recycling list auto-cleanup

Set up a "Recycling" smart list that auto-catches unwanted RSS articles, then schedule a daily purge at 8 AM (after Paperboy runs):

```
source:rss -is:fav age:>1d
```

The `cleanup-recycling.py` script finds all bookmarks in the list via `GET /lists/{listId}/bookmarks` and deletes them. The list's own query is the single source of truth — edit it in the Karakeep UI to change what gets deleted. See `references/recycling-cleanup-pattern.md` for setup details and the **critical smart list warning** (smart lists are saved searches, not containers — deleting matches hard-deletes from the entire system).

> **⚠️ CRITICAL: Verify search index before bulk deletion.** If the Karakeep search index is corrupted, every query returns ALL bookmarks regardless of filter. Running `cleanup-recycling.py` in this state will wipe your entire collection. Test with a negated query (`-source:rss` should return 0 results) before running. See karakeep skill's `references/search-index-recovery.md` for recovery steps.

> **⚠️ API endpoint selection for cleanup:** Use `GET /lists/{listId}/bookmarks` to find bookmarks in the Recycling list — it computes results from the list's stored query directly, matching what the Karakeep UI shows. Do NOT use `GET /bookmarks?query=...` (query silently ignored) or `GET /bookmarks/search?q=...` (returns fewer results than the list endpoint). The list's own query (editable in the Karakeep UI) is the single source of truth — no `RECYCLING_QUERY` env var needed.

> **Cron uses bash wrapper:** Following the same pattern as `paperboy.sh`, the cron job runs `cleanup-recycling.sh` which delegates to the skill-owned `cleanup-recycling.py`. Do NOT set the cron script directly to the `.py` file — the cron runner doesn't reliably execute Python scripts.

Key benefits:
- Runs at 8 AM, after Paperboy has already discovered and delivered articles (7:00-7:15)
- `no_agent` cron mode — always reliable, no agent overhead
- Silent on empty list — no noise when there's nothing to clean
- Hybrid approach: list endpoint for finding bookmarks + direct API delete for speed (~0.1s per delete)

### Rollback as Maintenance

When a feature change needs undoing, the proven pattern is:

1. **Roll back the open source repo** to a known-good commit:
   ```bash
   cd /tmp/paperboy-repo
   git reset --hard <target-commit>
   git push --force
   ```

2. **Copy files to local skills** — overwrite the local skill directory with the repo's version:
   ```bash
   cp <repo>/paperboy/paperboy.py <hermes>/skills/research/paperboy/scripts/paperboy.py
   cp <repo>/paperboy/SKILL.md <hermes>/skills/research/paperboy/SKILL.md
   cp <repo>/karakeep/SKILL.md <hermes>/skills/research/karakeep/SKILL.md
   ```

3. **Commit the local hermes-config repo** so both repos stay in sync:
   ```bash
   cd ~/.hermes
   git add -A skills/research/paperboy/ skills/research/karakeep/
   git commit -m "roll back paperboy to <commit-message>"
   git push
   ```

This avoids manually reverting individual code changes and guarantees the local skills match a known-good state.

## Session References

- `references/tag-scoring-fix-2026-05-24.md` — Tag scoring bug: Karakeep tags are dicts not strings; fix and TOP_TAGS_LIMIT removal
- `references/tag-format-pitfall.md` — Karakeep tags are dicts (`{"id":..., "name":...}`), not strings. Calling `.lower()` on them crashes scoring silently.
- `references/recycling-cleanup-pattern.md` — Recycling list auto-cleanup: smart list semantics, search index pre-flight, bulk-deletion safety, list-endpoint approach
- `references/tick-pacer-pattern.md` — Force agent-mode cron jobs to run within 5 minutes using a lightweight no_agent pacer job
- `references/cron-pitfalls-reference.md` — General Hermes cron pitfalls: agent-mode tick limitation, deliver target resolution, context_from chaining, per-job model overrides
- `references/cron-model-management.md` — Per-job model override management including the "no clear" workaround
- `references/tts-reliability-2026-05-23.md` — TTS generation step skipped by briefing agent; workarounds and mitigations
- `references/deliver-origin-noagent-fix-2026-05-23.md` — `deliver: origin` fails for no_agent mode cron jobs; fix with explicit `telegram:Dane` target
- `references/max-articles-unlimited-config.md` — `PAPERBOY_MAX_ARTICLES=-1` configuration for unlimited article delivery
- `references/context-from-clean-prompt.md` — Clean prompt pattern: Hermes auto-injects data location instructions via context_from, so prompts should only say *what to do* not *where to find it*
- `references/context-from-relay.md` — Moving from file-based relay to `context_from` chaining; eliminating `--output-file` from the wrapper script
- `references/env-var-config-and-briefing-polish-2026-05-23.md` — Env var configuration pattern, no-filter approach, briefing prompt evolution
- `references/paperboy-briefing-refinements-2026-05-22.md` — Briefing refinements, embedded links, scheduler unreliability
- `references/file-relay-cron-chaining.md` — (Legacy) File-based relay pattern; replaced by `context_from` chaining
- `references/agent-tts-news-report-setup-2026-05-22.md` — TTS news report agent delivery setup
- `references/cron-scheduler-unreliability-2026-05-22.md` — Scheduler bugs including agent-mode execution delays
- `references/date-filter-YYYY-MM-DD-only-2026-05-22.md` — Karakeep's `after:` filter limitation and the date-minus-1-day workaround
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