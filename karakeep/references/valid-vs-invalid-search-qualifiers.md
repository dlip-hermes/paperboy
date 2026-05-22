# Valid vs Invalid Karakeep Search Qualifiers

## The Bug: Silently Ignored Qualifiers

Karakeep CLI v0.32.0 **silently ignores** any qualifier that isn't in its supported list. It doesn't error — it just returns the most recent N bookmarks as if the filter wasn't there.

This means:
- `createdAt:>2026-05-21` → **ignored**, returns most recent bookmarks
- `modifiedAt:<2026-05-20` → **ignored**, returns most recent bookmarks
- Any other made-up qualifier → **silently ignored**

Only qualifiers documented in the CLI help or the official query language reference work.

## Valid Date Filtering

Use only:
- `after:<date>` — Created on or after the given date
- `before:<date>` — Created on or before the given date
- `age:<N[d|w|m|y]` — Filter by age (e.g. `age:<1d`, `age:>2w`)

## Timestamp Format

Both `after:` and `before:` accept:
- Date format: `after:2026-05-21`
- Full ISO 8601 timestamp: `after:2026-05-21T22:44:33.072Z`
- The `Z` suffix is accepted and treated as UTC

## Verification Test

To verify a qualifier works:

```bash
# Test with a future timestamp — should return 0
karakeep bookmarks search "after:2099-01-01" --json --limit 5

# If it returns any bookmarks, the qualifier is being ignored
```

## History

Discovered 2026-05-22 while debugging Paperboy's duplicate delivery issue. The paperboy script was using `createdAt:>{timestamp}` which was ignored by the CLI, causing every run to return the same set of articles regardless of the time filter.
