#!/usr/bin/env python3
"""Clean out the Recycling smart list — deletes all bookmarks in it."""

import json
import subprocess
import os
import sys

LIST_NAME = "Recycling"
KARAKEEP_URL = "https://karakeep.dex-lips.duckdns.org"

def run_karakeep(args):
    """Run a karakeep command and return parsed JSON."""
    env = os.environ.copy()
    env_path = os.path.expanduser('~/.hermes/.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k] = v
    env.setdefault('KARAKEEP_SERVER_ADDR', KARAKEEP_URL)

    cmd = ['npx', 'karakeep', '--server-addr', KARAKEEP_URL, '--json'] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        print(f"ERROR: {result.stderr.strip()}", file=sys.stderr)
        return None
    if not result.stdout.strip():
        return {}
    return json.loads(result.stdout)

def main():
    # Find the Recycling list
    lists = run_karakeep(['lists', 'list'])
    if not lists:
        print("Could not fetch lists.")
        return 1

    list_data = lists if isinstance(lists, list) else lists.get('lists', lists.get('data', []))
    recycling = None
    for lst in list_data:
        if isinstance(lst, dict) and lst.get('name') == LIST_NAME:
            recycling = lst
            break

    if not recycling:
        print(f"List '{LIST_NAME}' not found.")
        return 1

    list_id = recycling['id']
    print(f"Found list: {LIST_NAME} ({list_id})")

    # Get all bookmarks in the list
    result = run_karakeep(['bookmarks', 'search', f'list:{LIST_NAME}', '--limit', '100'])
    if not result:
        print("No bookmarks found or error querying.")
        return 0

    bookmarks = result.get('bookmarks', [])
    if not bookmarks:
        print(f"'{LIST_NAME}' is already empty. Nothing to delete.")
        return 0

    print(f"Deleting {len(bookmarks)} bookmark(s) from '{LIST_NAME}'...")
    deleted_count = 0
    for bm in bookmarks:
        bm_id = bm.get('id')
        title = (bm.get('title') or 'No title')[:50]
        if bm_id:
            del_result = run_karakeep(['bookmarks', 'delete', bm_id])
            if del_result is not None:
                deleted_count += 1
                print(f"  ✓ [{bm_id}] {title}")
            else:
                print(f"  ✗ [{bm_id}] {title} — delete failed")

    print(f"\nDone. Deleted {deleted_count}/{len(bookmarks)} bookmarks.")

    # Output a short summary for cron delivery
    if deleted_count > 0:
        print("---")
        print(f"♻️ Recycling bin emptied: {deleted_count} bookmark(s) deleted from '{LIST_NAME}'.")
    else:
        print("No bookmarks were deleted.")

    return 0

if __name__ == '__main__':
    sys.exit(main())
