#!/usr/bin/env bash
# Recycling bin auto-cleanup setup — scheduled deletion of all bookmarks in a Karakeep smart list
# Usage: bash setup-recycling.sh [--list "Recycling"] [--deliver origin]

set -euo pipefail

LIST="${2:-Recycling}"
DELIVER="${4:-origin}"

echo "♻️ Setting up Recycling bin auto-cleanup..."
echo "   List: $LIST"
echo "   Delivery: $DELIVER"
echo ""

# Copy the cleanup script
echo "📦 Installing cleanup script..."
mkdir -p ~/.hermes/scripts
cp paperboy/scripts/cleanup-recycling.py ~/.hermes/scripts/cleanup-recycling.py
chmod +x ~/.hermes/scripts/cleanup-recycling.py

# Verify the list exists
echo "🔍 Checking if list '$LIST' exists in Karakeep..."
LIST_ID=$(npx karakeep --json lists list 2>/dev/null | python3 -c "
import json,sys
data = json.load(sys.stdin)
lists = data if isinstance(data, list) else data.get('lists', data.get('data', []))
for lst in lists:
    if isinstance(lst, dict) and lst.get('name') == '$LIST':
        print(lst.get('id', ''))
" 2>/dev/null || echo "")

if [ -n "$LIST_ID" ]; then
    echo "   ✓ Found '$LIST' (ID: $LIST_ID)"
else
    echo "   ⚠️  List '$LIST' not found. You'll need to create it in Karakeep first."
    echo "      The cron job will still be created but will error until the list exists."
fi

# Create or update the cron job
echo "⏰ Scheduling daily cleanup at 8:00 AM..."
hermes cron create \
    --name recycling-cleanup \
    --script cleanup-recycling.py \
    --schedule "0 8 * * *" \
    --deliver "$DELIVER" \
    --no-agent 2>/dev/null || {
    echo "  ↳ Updating existing job..."
    JOB_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "recycling-cleanup"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
    if [ -n "$JOB_ID" ]; then
        hermes cron update "$JOB_ID" --script cleanup-recycling.py --schedule "0 8 * * *" --deliver "$DELIVER" --no-agent
    fi
}

echo ""
echo "✅ Recycling cleanup configured!"
echo ""
echo "📋 Every day at 8:00 AM, all bookmarks in the '$LIST' smart list will be deleted."
echo "   To customize the list name, run: bash setup-recycling.sh --list \"Your List\""
echo ""
echo "🚀 Run it now to clear the list immediately:"
echo "   python3 ~/.hermes/scripts/cleanup-recycling.py"