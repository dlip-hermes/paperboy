---
name: karakeep
description: Use when interacting with Karakeep (bookmark manager) — adding bookmarks, managing lists/tags, searching via query language, RSS feeds, CLI automation, or webhooks.
version: 1.0.0
author: ClawHub / karakeep
license: MIT
metadata:
  hermes:
    tags: [bookmarks, cli, productivity, rss, automation]
    related_skills: []
---

# Karakeep

[Karakeep](https://karakeep.com) is an open-source self-hosted bookmark manager for collecting, organizing, and searching content.

## When to Use

- Adding/managing bookmarks (links, text, media)
- Organizing bookmarks into lists and tagging them
- Searching with Karakeep's query language
- Consuming or publishing RSS feeds
- Setting up automation rules and webhooks
- Using the `@karakeep/cli` npm package

## Core Concepts

### Bookmark Types
- **Links**: URLs with auto-fetched title, description, image, screenshot, and full-page archive
- **Text**: Quick notes or text snippets
- **Media**: Images and PDFs uploaded directly

### CLI Usage Patterns (Learned from Production)
- **JSON Flag Required**: All Karakeep CLI commands that need machine-readable output MUST use the `--json` flag. Without it, output is human-readable text that's difficult to parse.
- **Server Address Handling**: The CLI requires explicit `--server-addr` flag or environment variable `KARAKEEP_SERVER_ADDR`. Using bare "karakeep" without server specification often fails with auth errors.
- **Authentication**: API key can be passed via `--api-key` flag or `KARAKEEP_API_KEY` environment variable. Environment variables are preferred for security.
- **Search vs List**: The `bookmarks search` command sometimes fails with "Failed to parse URL" server-side errors. When this happens, use `bookmarks list --include-content` and filter results manually.
- **Tag Format**: Tags can be added with `--tag-name` flag (repeatable for multiple tags). The CLI accepts both plain tags and quoted tags containing spaces.

### Features
- **Favorites**: Star bookmarks for quick access
- **Archiving**: Hide from homepage while keeping searchable
- **Notes**: Personal context attached to any bookmark
- **Highlights**: Save quotes, summaries, TODOs while reading — searchable across all bookmarks

### Lists
- **Manual lists**: Curated collections by project/topic (private or public)
- **Smart lists**: Auto-updating via search queries (e.g. `#ai -archived`)
- **Collaboration**: Invite editors (can add) or viewers (read-only)

### Tags
Lightweight labels (topics, sources, workflow states). Multiple per bookmark, travel with bookmarks across lists. AI can auto-generate tags.

### RSS Feeds
- **Consuming**: Auto-monitor external RSS feeds, create bookmarks from new items (hourly, with dedup)
- **Publishing**: Export any list as RSS feed with unique token

### Automation
- **Rule Engine**: If-this-then-that to auto-tag, favorite, or route bookmarks
- **Webhooks**: Subscribe to bookmark events (add/update/archive)

## CLI Installation

```bash
npm install -g @karakeep/cli
```

Or via Docker:
```bash
docker run --rm ghcr.io/karakeep-app/karakeep-cli:release --help
```

## Authentication

**Option 1 — Environment variables (recommended):**
```bash
export KARAKEEP_API_KEY="..."
export KARAKEEP_SERVER_ADDR="https://cloud.karakeep.com"  # optional, defaults to cloud
```

**Option 2 — CLI flags:**
```bash
karakeep --api-key <key> --server-addr <addr> <command>
```

**Important:** To get JSON output suitable for scripting, always use the `--json` flag:
```bash
karakeep --server-addr https://your.karakeep.instance --json whoami
```

**Verify:**
```bash
karakeep whoami
```

Get your API key from Karakeep instance settings page.

## Bookmark Commands

```bash
# Add a link bookmark
karakeep bookmarks add --link "https://example.com"

# Add with tags and to a specific list
karakeep bookmarks add --link "https://example.com" --tag-name "reading" --list-id <list-id>

# Add a text bookmark
karakeep bookmarks add --note "Remember to review the PR"

# Get bookmark details
karakeep bookmarks get <bookmark-id>

# List bookmarks (with optional query filter)
karakeep bookmarks list --query "is:fav #important"

# Archive/unarchive
karakeep bookmarks archive <bookmark-id>
karakeep bookmarks unarchive <bookmark-id>

# Add/remove tags
karakeep bookmarks add-tag <bookmark-id> --tag-name "work"
karakeep bookmarks remove-tag <bookmark-id> --tag-name "work"
```

Run `karakeep --help` for all available commands.

## Search Query Language

### Basic Syntax
- Spaces between conditions = implicit AND
- Use `and` / `or` for explicit boolean logic
- Prefix qualifiers with `-` or `!` to negate (e.g. `-is:archived`, `!is:fav`)
- Use `()` for grouping (groups can't be negated)
- Unqualified text = full-text search

### Qualifiers

| Qualifier | Description | Example |
|-----------|-------------|---------|
| `is:fav` | Favorited bookmarks | `is:fav` |
| `is:archived` | Archived bookmarks | `-is:archived` |
| `is:tagged` | Bookmarks with one or more tags | `is:tagged` |
| `is:inlist` | Bookmarks in one or more lists | `is:inlist` |
| `is:link` | Link bookmarks | `is:link` |
| `is:text` | Text/note bookmarks | `is:text` |
| `is:media` | Media bookmarks (images/PDFs) | `is:media` |
| `is:broken` | Failed crawls or non-2xx status | `is:broken` |
| `url:<value>` | Match URL substring | `url:github.com` |
| `title:<value>` | Match title substring | `title:rust`, `title:"my title"` |
| `#<tag>` or `tag:<tag>` | Match specific tag | `#important`, `tag:"work in progress"` |
| `list:<name>` | Match bookmarks in a list | `list:reading`, `list:"to review"` |
| `after:<date>` | Created on or after (YYYY-MM-DD) | `after:2024-01-01` |
| `before:<date>` | Created on or before (YYYY-MM-DD) | `before:2024-12-31` |
| `age:<time-range>` | Filter by age. `<` = max, `>` = min. Units: `d/w/m/y` | `age:<1d`, `age:>2w`, `age:<6m` |
| `feed:<name>` | Bookmarks from specific RSS feed | `feed:Hackernews` |
| `source:<value>` | Match capture source: `api`, `web`, `cli`, `mobile`, `extension`, `singlefile`, `rss`, `import` | `source:rss`, `-source:web` |

### Example Queries

```bash
# Favorited bookmarks from 2024 tagged "important"
is:fav after:2024-01-01 before:2024-12-31 #important

# Archived bookmarks in "reading" list or tagged "work"
is:archived and (list:reading or #work)

# Untagged or unorganized bookmarks
-is:tagged or -is:inlist

# Recent bookmarks from the last week
age:<1w

# Full-text search with qualifiers
machine learning is:fav -is:archived
```

## List Commands

```bash
# Create a manual list
karakeep lists create --name "Reading List"

# Create a smart list (auto-updating query)
karakeep lists create --name "AI News" --query "#ai -is:archived"

# Get list details
karakeep lists get <list-id>

# Invite collaborators
karakeep lists invite <list-id> --email "colleague@example.com" --role "editor"

# Add bookmark to list
karakeep lists add-bookmark <list-id> --bookmark-id <bookmark-id>
```

### Common Pitfalls

1. **Forgetting to set API key**: Commands fail with auth errors. Use `karakeep whoami` to verify.
2. **Smart list query syntax errors**: Start simple, test incrementally. Use `--query` flag with quotes.
3. **Tag vs list confusion**: Tags are lightweight (multiple per bookmark), lists are containers (bookmarks belong to them).
4. **Duplicate RSS items**: Karakeep has built-in dedup by URL/title combo — but within a short time window, not forever.
5. **Missing JSON flag for scripting**: When using Karakeep CLI in scripts, always use `--json` flag for machine-readable output.
6. **`bookmarks search` broken (server-side URL parse error)**: If you get "Failed to parse URL" errors on search, use `bookmarks list` instead and filter in Python. The `--limit` flag does NOT exist on `list` — only `--include-archived` and `--include-content`.
7. **ENV var required for JSON output**: Some endpoints require `export KARAKEEP_SERVER_ADDR="https://your.server"` before the `--server-addr` flag works reliably for JSON output. Test with `karakeep --json whoami` first.
8. **CLI v0.31.0 has no `delete` subcommand**: The `karakeep bookmarks delete <id>` command does NOT exist in v0.31.0 despite being documented in some references. The tRPC endpoint `bookmarks.deleteBookmark` exists server-side but requires a write-capable API key. Use the Karakeep web UI for deletion.
9. **Read-only API key (`ak2_` prefix)**: API keys starting with `ak2_` can read but may not write. Destructive operations (delete) return "Bookmark not found" while reads work. The `bookmarks update --note` command DOES work with read-only keys (uses a different endpoint). For full write access, generate a new key in Karakeep settings.
10. **`requests` module not available in Nix environment**: When writing Python scripts that call Karakeep or other APIs, use `urllib.request` from stdlib instead of `requests`. The `requests` package is not installed in the Nix Python environment. Alternatively, shell out to `curl` via `subprocess.run()`.
11. **`createdAt:>`, `modifiedAt:>` and similar qualifiers are silently ignored**: The only valid date-filtering qualifiers are `after:<date>` and `before:<date>`. Any other syntax like `createdAt:>2026-05-21` or `modifiedAt:<2026-05-20` is **silently ignored** by the CLI — it just returns the most recent N bookmarks regardless. If you use these in a script, you'll get incorrect results without any error message. Always use `after:` / `before:` for date filtering. The `after:` qualifier accepts full ISO 8601 timestamps like `after:2026-05-21T22:44:33.072Z` in addition to `after:2026-05-21` date format.

## Automation & Advanced Usage\n\nSee `references/article-discovery.md` for a complete workflow to automatically discover and add articles based on your favorited bookmarks.\n\n## Scripting Best Practices\n\nWhen using Karakeep CLI in scripts and automation:\n\n1. **Always use `--json` flag** for machine-readable output suitable for parsing\n2. **Handle authentication properly** via environment variables or config files\n3. **Implement error handling** for network issues, rate limiting, and unexpected responses\n4. **Add rate limiting** between requests to be respectful to the service\n5. **Validate output structure** before accessing fields to prevent script failures\n\nExample patterns:\n```bash\n# Get JSON output for parsing\nkarakeep --server-addr https://your.instance --json bookmarks search \"is:fav\"\n\n# In Python scripts, parse JSON safely:\nimport json, subprocess\nresult = subprocess.run([\"karakeep\", \"--server-addr\", \"https://instance\", \"--json\", \"bookmarks\", \"search\", \"is:fav\"], capture_output=True, text=True)\ndata = json.loads(result.stdout) if result.returncode == 0 else []\n```\n\nSee `references/article-discovery.md` for complete workflow implementations.
See `references/valid-vs-invalid-search-qualifiers.md` for the difference between supported and silently-ignored search qualifiers.

## One-Shot Recipes

**Add a link with tags and put it in a list:**
```bash
KARAKEEP_API_KEY="your-key" karakeep bookmarks add \
  --link "https://example.com/article" \
  --tag-name "reading" \
  --tag-name "ai" \
  --list-id <your-list-id>
```

**Find all broken bookmarks and fix them:**
```bash
karakeep bookmarks list --query "is:broken" --format json | \
  jq -r '.bookmarks[].id' | while read id; do
    karakeep bookmarks recrawl $id
  done
```

**Export a list as RSS:**
```bash
karakeep lists rss-token <list-id>
# Returns unique RSS URL for that list
```