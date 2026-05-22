#!/usr/bin/env bash
# Paperboy setup script — installs skill files and configures both cron jobs
# Usage: bash setup-cron.sh [--deliver target]
#   --deliver target   Where to deliver (default: origin — auto-detect current chat)
#                      Examples: origin, telegram:Dane, telegram:-1001234567890

set -euo pipefail

DELIVER="${2:-origin}"

echo "📦 Installing Paperboy skill..."
mkdir -p ~/.hermes/skills/research/paperboy/scripts
cp -r paperboy/SKILL.md ~/.hermes/skills/research/paperboy/
cp -r paperboy/paperboy.py ~/.hermes/skills/research/paperboy/scripts/

echo "📦 Installing Karakeep skill (dependency)..."
mkdir -p ~/.hermes/skills/research/karakeep
cp -r karakeep/SKILL.md ~/.hermes/skills/research/karakeep/

echo "🔧 Creating bash wrapper script..."
mkdir -p ~/.hermes/scripts
cat > ~/.hermes/scripts/paperboy.sh << 'WRAPPER'
#!/bin/bash
# Paperboy launcher — delegates to the skill-owned Python script
# Writes to .paperboy/paperboy.md for follow-up agent job to pick up
export PAPERBOY_MAX_ARTICLES=50
export PAPERBOY_TOP_TAGS_LIMIT=20
exec /var/lib/hermes/.nix-profile/bin/python3 \
  ~/.hermes/skills/research/paperboy/scripts/paperboy.py \
  --output-file ~/.hermes/.paperboy/paperboy.md
WRAPPER
chmod +x ~/.hermes/scripts/paperboy.sh

echo "📁 Creating state directory..."
mkdir -p ~/.hermes/.paperboy

echo "⏰ Creating cron job: paperboy (7:00 AM — raw delivery)..."
hermes cron create \
  --name paperboy \
  --script paperboy.sh \
  --schedule "0 7 * * *" \
  --deliver "$DELIVER" \
  --no-agent 2>/dev/null || {
    echo "  ↳ Updating existing job instead..."
    # Find the existing paperboy job ID
    RAW_ID=$(hermes cron list 2>/dev/null | grep -A1 '"name": "paperboy"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
    if [ -n "$RAW_ID" ]; then
      hermes cron update "$RAW_ID" --no-agent --schedule "0 7 * * *" --deliver "$DELIVER" --name paperboy --script paperboy.sh
    fi
  }

echo "⏰ Creating cron job: paperboy-briefing (7:15 AM — radio + TTS)..."
hermes cron create \
  --name paperboy-briefing \
  --schedule "15 7 * * *" \
  --deliver "$DELIVER" \
  --skills paperboy \
  --prompt "The paperboy cron job ran at 7 AM and wrote its output to ~/.hermes/.paperboy/paperboy.md. Read that file. If the file contains \"Sorry mate there's no new news at the moment\", just forward that message verbatim via send_message() (no audio needed). STOP after that. Otherwise: (1) Compose a radio-style news briefing from the articles. For each article, embed its preview URL as a markdown link on the title text so it's tappable but the raw URL is hidden — e.g. [Article Title](url) followed by a short conversational summary. (2) Send the full transcript as a text message. (3) Generate TTS audio of just the spoken portion (no URLs, no markdown) using text_to_speech(). (4) Send the audio file via send_message() with MEDIA:path in the message text." 2>/dev/null || {
    echo "  ↳ Updating existing job instead..."
    BRIEFING_ID=$(hermes cron list 2>/dev/null | grep -A1 '"name": "paperboy-briefing"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
    if [ -n "$BRIEFING_ID" ]; then
      hermes cron update "$BRIEFING_ID" --schedule "15 7 * * *" --deliver "$DELIVER" --name paperboy-briefing --skills paperboy --prompt "..."
    fi
  }

echo ""
echo "✅ Paperboy setup complete!"
echo ""
echo "📋 Cron jobs configured:"
echo "   7:00 AM — paperboy         (raw article list, no_agent mode)"
echo "   7:15 AM — paperboy-briefing (radio briefing + TTS audio)"
echo ""
echo "🔗 Chaining context_from (so briefing has fallback data):"
RAW_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "paperboy"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
BRIEFING_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "paperboy-briefing"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
if [ -n "$RAW_ID" ] && [ -n "$BRIEFING_ID" ]; then
  hermes cron update "$BRIEFING_ID" --context-from "$RAW_ID"
  echo "   Done! (paperboy-briefing will receive paperboy output as fallback context)"
fi

echo ""
echo "🚀 Next run: Tomorrow at 7:00 AM (paperboy) + 7:15 AM (paperboy-briefing)"
