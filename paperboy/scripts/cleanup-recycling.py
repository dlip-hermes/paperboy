#!/usr/bin/env python3
"""Clean out the Recycling smart list — deletes ALL bookmarks in the list.

Uses GET /lists/{listId}/bookmarks — the same endpoint the Karakeep UI uses.
The list's own query is the single source of truth.
"""

import json
import os
import sys
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

LIST_NAME = "Recycling"
KARAKEEP_URL = "https://karakeep.dex-lips.duckdns.org"

def load_api_key():
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("KARAKEEP_API_KEY="):
                    return line.split("=", 1)[1]
    return os.environ.get("KARAKEEP_API_KEY", "")

API_KEY = load_api_key()

def api_request(method, path, params=None):
    url = f"{KARAKEEP_URL}/api/v1{path}"
    if params:
        url += "?" + urlencode(params)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    req = Request(url, headers=headers, method=method)
    try:
        with urlopen(req, timeout=15) as resp:
            if resp.status == 204:
                return {}
            raw = resp.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except HTTPError as e:
        print(f"  ✗ API {method} {path}: {e.code} {e.reason}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  ✗ API {method} {path}: {e}", file=sys.stderr)
        return None

def delete_bookmark(bm_id):
    url = f"{KARAKEEP_URL}/api/v1/bookmarks/{bm_id}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    req = Request(url, headers=headers, method="DELETE")
    try:
        with urlopen(req, timeout=15) as resp:
            return resp.status in (200, 204)
    except HTTPError as e:
        print(f"  ✗ DELETE /bookmarks/{bm_id}: {e.code} {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  ✗ DELETE /bookmarks/{bm_id}: {e}", file=sys.stderr)
        return False

def main():
    lists = api_request("GET", "/lists")
    if not lists:
        print("Could not fetch lists.")
        return 1

    list_id = None
    list_query = ""
    for l in lists.get("lists", []):
        if l.get("name") == LIST_NAME:
            list_id = l["id"]
            list_query = l.get("query", "")
            break

    if not list_id:
        print(f"List '{LIST_NAME}' not found.")
        return 1

    print(f"Recycling cleanup — clearing list '{LIST_NAME}' (query: {list_query})")

    all_bookmarks = []
    cursor = None
    while True:
        params = {"limit": 100}
        if cursor:
            params["cursor"] = cursor
        result = api_request("GET", f"/lists/{list_id}/bookmarks", params=params)
        if result is None:
            print("Could not fetch bookmarks from list.")
            return 1
        bookmarks = result.get("bookmarks", [])
        all_bookmarks.extend(bookmarks)
        cursor = result.get("nextCursor")
        if not cursor or not bookmarks:
            break

    if not all_bookmarks:
        print("List is already empty. Nothing to delete.")
        return 0

    print(f"Found {len(all_bookmarks)} bookmark(s) to delete...")

    total_deleted = 0
    total_failed = 0
    for bm in all_bookmarks:
        bm_id = bm.get("id")
        title = (bm.get("title") or "No title")[:50]
        if bm_id:
            if delete_bookmark(bm_id):
                total_deleted += 1
            else:
                total_failed += 1
                print(f"  ✗ [{bm_id}] {title}")

    print(f"\nDone. Deleted {total_deleted} bookmark(s)"
          f"{f', {total_failed} failed' if total_failed else ''}.")

    if total_deleted > 0:
        print("---")
        print(f"♻️ Recycling bin emptied: {total_deleted} bookmark(s) deleted.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
