# Search Index Recovery

## Symptoms of a Corrupted Search Index

After a database restore, the Karakeep search index may be corrupted. All queries return the same results regardless of search terms:

- `GET /bookmarks?query=source:rss` returns all bookmarks (not just RSS)
- `GET /bookmarks?query=zzzzzzzzz` (nonsense) returns results
- `-source:rss` returns items with `source:rss`
- `is:fav` returns items with `favourited:false`
- All queries returns identical sets of bookmarks

## Quick Diagnosis

```bash
# These should return DIFFERENT counts
curl -s "https://<instance>/api/v1/bookmarks/search?q=source:rss&limit=5" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"

curl -s "https://<instance>/api/v1/bookmarks/search?q=-source:rss&limit=5" \
  -H "Authorization: Bearer $KARAKEEP_API_KEY"
```

If both return the same items, the search index is corrupt.

## Recovery via CLI

```bash
# Queue a full reindex
npx karakeep --server-addr <instance> admin jobs reindex-all

# Monitor progress
npx karakeep --server-addr <instance> admin jobs stats
```

The reindex job is backgrounded. Wait until "Search Indexing" queued count drops to 0. If the count stays stuck, the workers may need a service restart.

## Safety Rules

- **Never** run bulk-deletion scripts without first verifying the search index is healthy
- Always run a diagnosis before any automated cleanup
- The `GET /bookmarks/search?q=...` endpoint is the only API endpoint that applies search filters
- The CLI `bookmarks search` command internally hits this endpoint and is reliable
