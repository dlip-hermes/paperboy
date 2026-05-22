# 🏃💨 Paperboy — Automated Article Discovery from Karakeep

Paperboy is an automated workflow that discovers articles from your [Karakeep](https://github.com/karakeep-app/karakeep) bookmark manager based on your favorited bookmarks and delivers them with title, summary, and preview link.

Originally built as a skill for [Hermes Agent](https://hermes-agent.nousresearch.com), Paperboy can run standalone via cron or any scheduler.

## Features

- **Interest Analysis** — Extracts and analyzes tags from your favorited bookmarks to determine current interests (weighted by frequency)
- **Recent Article Detection** — Finds articles bookmarked since the last run using Karakeep's `after:` date filter plus client-side validation
- **Tag-Based Scoring** — Scores articles based on tag relevance with frequency weighting, substring matching, and word overlap for multi-word tags
- **Preview URL Generation** — Generates dashboard preview URLs for the top N scored articles (default: 10)
- **Deduplication via Date Tracking** — Each run only processes articles bookmarked since the last check

## How It Works

1. **Fetch** all favorited bookmarks from Karakeep
2. **Extract & rank** tags by frequency (excluding generic tags like "inbox")
3. **Query** Karakeep for bookmarks created since the last run (`after:<timestamp>`)
4. **Score** each new article against your interest tags
5. **Select** the top N articles (default: 10)
6. **Output** formatted title, summary, and preview URL for each
7. **Save** the current time as the last run for next execution

## Usage

### Prerequisites

- Python 3.6+
- A [Karakeep](https://github.com/karakeep-app/karakeep) instance with API access
- Karakeep CLI installed (`npm install -g @karakeep/cli`)

### Environment Variables

```bash
export KARAKEEP_SERVER_ADDR="https://your-karakeep-instance.example.com"
export KARAKEEP_API_KEY="your-api-key"
```

### Run

```bash
python3 paperboy.py
```

The script outputs the delivery title followed by article details. If no new articles are found, it outputs nothing (exit code 0).

### Schedule with Cron

```bash
# Run daily at 7:00 AM
0 7 * * * cd /path/to/paperboy && python3 paperboy.py
```

## Output Format

```
# 🏃💨 Paperboy Run! 🗞️

## Article Title

Article summary text here.

https://karakeep.example.com/dashboard/preview/<bookmark_id>

## Next Article Title

...
```

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ARTICLES` | 10 | Maximum articles to deliver per run |
| `TOP_TAGS_LIMIT` | 8 | Number of interest tags to use for scoring |
| `EXCLUDED_TAGS` | `{'inbox'}` | Tags to ignore when ranking interests |
| State file | `~/.hermes/.article_discovery/strategy_state.json` | Tracks last run time (`last_run` field, stored in local time) |

## Known Issues

- **Karakeep CLI `createdAt:>` is broken** — The `createdAt:>{timestamp}` matcher is ignored by Karakeep CLI v0.32.0. Use `after:{timestamp}` instead. The script handles this but note if using the CLI directly.
- **Hardcoded domain** — Preview URLs use `karakeep.dex-lips.duckdns.org`. For other instances, edit the URL template in the script.
- **No summary truncation** — Long summaries are output verbatim.

## License

MIT
