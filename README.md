# 📚 Karakeep Skills for Hermes Agent

Hermes Agent skills for working with [Karakeep](https://github.com/karakeep-app/karakeep), the open-source bookmark manager.

## Contents

| Folder | Description |
|--------|-------------|
| `paperboy/` | 🏃💨 Automated article discovery — fetches favorited bookmarks, ranks your interests, finds new articles, and delivers previews |
| `karakeep/` | Comprehensive Karakeep skill — CLI commands, query language reference, automation patterns, and troubleshooting |

## Installation for Hermes Agent

Copy both skill folders to your Hermes skills directory:

```bash
cp -r paperboy ~/.hermes/skills/research/
cp -r karakeep ~/.hermes/skills/research/
```

Then the skills are available via `hermes` commands and your agent can load them with `skill_view(name='paperboy')` or `skill_view(name='karakeep')`.

---

# 🏃💨 Paperboy — Automated Article Discovery

Paperboy discovers articles from your Karakeep bookmarks based on your favorited bookmark tags and delivers them with title, summary, and preview link.

### Features

- **Interest Analysis** — Extracts and ranks tags from your favorited bookmarks (frequency-weighted)
- **Recent Article Detection** — Finds articles bookmarked since the last run using Karakeep's `after:` date filter plus client-side validation
- **Tag-Based Scoring** — Scores articles by tag relevance with substring and word-overlap matching
- **Preview URL Generation** — Dashboard preview links for the top N scored articles (default: 10)

### How It Works

1. Fetches all favorited bookmarks from Karakeep
2. Extracts & ranks tags by frequency (excludes generic tags like "inbox")
3. Queries Karakeep for bookmarks created since the last run (`after:<timestamp>`)
4. Scores each new article against your interest tags
5. Outputs the top 10 with formatted title, summary, and preview URL
6. Saves the current time as the last run for next execution

### Standalone Usage

```bash
# Prerequisites
export KARAKEEP_SERVER_ADDR="https://your-karakeep-instance.example.com"
export KARAKEEP_API_KEY="your-api-key"

# Run
python3 paperboy/paperboy.py

# Or schedule with cron
0 7 * * * cd /path/to/repo && python3 paperboy/paperboy.py
```

### Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_ARTICLES` | 10 | Maximum articles to deliver per run |
| `TOP_TAGS_LIMIT` | 8 | Number of interest tags to use for scoring |
| `EXCLUDED_TAGS` | `{'inbox'}` | Tags to ignore when ranking interests |
| State file | `~/.hermes/.article_discovery/strategy_state.json` | Tracks last run time |

---

# 🔖 Karakeep Skill

A comprehensive reference for the Karakeep CLI — command reference, search query language, automation patterns, scripting best practices, and common pitfalls.

See `karakeep/SKILL.md` for full documentation.

## Search Query Language Quick Reference

| Qualifier | Description | Example |
|-----------|-------------|---------|
| `is:fav` | Favorited bookmarks | `is:fav` |
| `is:archived` | Archived bookmarks | `-is:archived` |
| `is:link` / `is:text` / `is:media` | Bookmark type | `is:link` |
| `is:broken` | Failed crawls | `is:broken` |
| `#<tag>` or `tag:<tag>` | Match specific tag | `#important` |
| `list:<name>` | Bookmarks in a list | `list:reading` |
| `after:<date>` | Created on or after | `after:2024-01-01` |
| `before:<date>` | Created on or before | `before:2024-12-31` |
| `age:<time-range>` | Filter by age (d/w/m/y) | `age:<1d` |
| `url:<value>` | URL substring | `url:github.com` |
| `title:<value>` | Title substring | `title:rust` |
| `feed:<name>` | From RSS feed | `feed:Hackernews` |

> **⚠️ Important:** `createdAt:>`, `modifiedAt:>` and similar qualifiers are silently ignored by the CLI. Always use `after:` / `before:` for date filtering.

## License

MIT