# Karakeep REST API Reference

Official API docs: https://github.com/karakeep-app/karakeep/tree/main/docs/docs/api

## Authentication

All endpoints require a Bearer token in the `Authorization` header. Generate an API key from the Karakeep web UI under **Settings → API Keys**.

```
Authorization: Bearer <api_key>
```

## Pagination

List endpoints use cursor-based pagination:
- `cursor` — pass the `nextCursor` from the previous response
- `limit` — maximum items per page
- Response includes `nextCursor` — `null` means no more results

## Bookmark Types

| Type | Description |
|------|-------------|
| `link` | URL bookmark with crawled metadata (title, description, author, etc.) |
| `text` | Plain text note |
| `asset` | Uploaded file (image or PDF) |

## Endpoints

### GET /lists

Get all lists for the authenticated user.

```bash
curl -s "https://<instance>/api/v1/lists" -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

Response: `{ "lists": [...] }` — each list has `id`, `name`, `type` (`manual`/`smart`), `query` (smart lists), `icon`, etc.

### GET /lists/{listId}/bookmarks

Get bookmarks in a specific list. For smart lists, results are computed from the list's search query.

```bash
curl -s "https://<instance>/api/v1/lists/<listId>/bookmarks?limit=50&cursor=<cursor>" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

### GET /bookmarks

⚠️ **This endpoint does NOT support a `query` parameter.** The API docs define only `archived`, `favourited`, `sortOrder`, `limit`, `cursor`, and `includeContent` as supported parameters. Passing `?query=...` is silently ignored and returns ALL bookmarks.

Use `GET /bookmarks/search` for filtered queries (see below).

```bash
# List all bookmarks (paginated)
curl -s "https://<instance>/api/v1/bookmarks?limit=50&cursor=<cursor>" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"

# Filter by archived/favorited only
curl -s "https://<instance>/api/v1/bookmarks?favourited=true&limit=50" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

### GET /bookmarks/search

Search bookmarks across titles, content, descriptions, and notes. Uses the `q` parameter (NOT `query`).

```bash
curl -s "https://<instance>/api/v1/bookmarks/search?q=source:rss+-is:fav&limit=50&sortOrder=desc" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

Parameters:
- `q` (required) — search query
- `sortOrder` — `asc`, `desc`, or `relevance` (default)
- `limit` — max items per page
- `cursor` — pagination cursor
- `includeContent` — set to `true` to include full content

### GET /bookmarks/{bookmarkId}

Get a single bookmark by ID.

```bash
curl -s "https://<instance>/api/v1/bookmarks/<id>" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

### POST /bookmarks

Create a new bookmark.

```bash
# Link bookmark
curl -s -X POST "https://<instance>/api/v1/bookmarks" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"link","url":"https://example.com"}'

# Text bookmark
curl -s -X POST "https://<instance>/api/v1/bookmarks" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type":"text","text":"Remember to do X"}'
```

### PATCH /bookmarks/{bookmarkId}

Partially update a bookmark. Only the fields you want to change need to be provided.

```bash
curl -s -X PATCH "https://<instance>/api/v1/bookmarks/<id>" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"favourited":true,"title":"New Title"}'
```

Updatable fields: `archived`, `favourited`, `title`, `note`, `summary`, `createdAt`, `url`, `description`, `author`, `publisher`, `datePublished`, `dateModified`, `text`, `assetContent`.

### DELETE /bookmarks/{bookmarkId}

⚠️ **Hard delete — permanent and irreversible. No trash/archive for deleted bookmarks.**

```bash
curl -s -X DELETE "https://<instance>/api/v1/bookmarks/<id>" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

## Recommended Pattern for Automated Scripts

Due to `GET /bookmarks?query=` being silently ignored and `GET /bookmarks/search` having result-count divergence from list queries, use this approach for safe bulk operations:

**Preferred: Use `GET /lists/{listId}/bookmarks`** — this endpoint computes results from the list's stored query directly (same mechanism the Karakeep UI uses). It returns the most accurate results and respects the list's query exactly.

```python
import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode

def get_list_bookmarks(list_name, api_key, base_url):
    """Get all bookmarks in a named list, using the list's own query."""
    # 1. Find the list ID by name
    req = Request(f"{base_url}/api/v1/lists",
                  headers={"Authorization": f"Bearer {api_key}"})
    with urlopen(req) as resp:
        lists = json.loads(resp.read()).get("lists", [])
    list_id = next(l["id"] for l in lists if l["name"] == list_name)

    # 2. Paginate through the list's bookmarks
    all_bookmarks = []
    cursor = None
    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        url = f"{base_url}/api/v1/lists/{list_id}/bookmarks?{urlencode(params)}"
        req = Request(url, headers={"Authorization": f"Bearer {api_key}"})
        with urlopen(req) as resp:
            d = json.loads(resp.read())
        bookmarks = d.get("bookmarks", [])
        all_bookmarks.extend(bookmarks)
        cursor = d.get("nextCursor")
        if not cursor or not bookmarks:
            break
    return all_bookmarks

def delete_bookmark(bm_id, api_key, base_url):
    """Delete via REST API (fast, no npx overhead)."""
    url = f"{base_url}/api/v1/bookmarks/{bm_id}"
    req = Request(url,
                  headers={"Authorization": f"Bearer {api_key}"},
                  method="DELETE")
    with urlopen(req, timeout=15) as resp:
        return resp.status in (200, 204)
```

**Fallback: CLI search + API delete** — use only when you need an ad-hoc query not tied to an existing list:

```python
import json, subprocess

def search_bookmarks(query, base_url):
    """Search via CLI (reliable filtering, but may miss items vs list endpoint)."""
    cmd = ["npx", "karakeep", "--server-addr", base_url, "--json",
           "bookmarks", "search", "--", query, "--limit", "1000"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout).get("bookmarks", [])
```

See `cleanup-recycling.py` in the paperboy skill for a complete implementation.

## What NOT to do

- ❌ `GET /bookmarks?query=source:rss` — query is silently ignored
- ❌ `POST /bookmarks/search` with JSON body — returns 404
- ❌ Bulk-delete without verifying the search index is healthy first
- ❌ Trust `GET /bookmarks/search` for accurate list counts — it can return fewer results than `GET /lists/{listId}/bookmarks` for the same query (observed: 20 vs 31 for the Recycling list). The list endpoint computes from the stored query and is more reliable for list-specific operations.
