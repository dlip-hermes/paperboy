#!/usr/bin/env bash
# Paperboy setup script — installs skill files and configures both cron jobs
# Usage: bash setup-cron.sh [--deliver target]
#   --deliver target   Where to deliver (default: origin — auto-detect current chat)
#                      Examples: origin, telegram:Dane, telegram:-1001234567890

set -euo pipefail

DELIVER="origin"
while [[ $# -gt 0 ]]; do
    case "$1" in
        --deliver) DELIVER="$2"; shift 2 ;;
        *) shift ;;
    esac
done

PYTHON="${PYTHON:-python3}"  # override for NixOS: PYTHON=/var/lib/hermes/.nix-profile/bin/python3

echo "📦 Installing Paperboy skill..."
mkdir -p ~/.hermes/skills/research/paperboy/scripts
cp -r paperboy/SKILL.md ~/.hermes/skills/research/paperboy/
cp -r paperboy/scripts/* ~/.hermes/skills/research/paperboy/scripts/

echo "📦 Installing Karakeep skill (dependency)..."
mkdir -p ~/.hermes/skills/research/karakeep/references
cp -r karakeep/SKILL.md ~/.hermes/skills/research/karakeep/
cp -r karakeep/references/* ~/.hermes/skills/research/karakeep/references/ 2>/dev/null || true

echo "🔧 Creating bash wrapper scripts..."
mkdir -p ~/.hermes/scripts

# Paperboy wrapper
cat > ~/.hermes/scripts/paperboy.sh << WRAPPER
#!/bin/bash
# Paperboy launcher — delegates to the skill-owned Python script
# Output is captured by Hermes cron and injected into briefing via context_from
export PAPERBOY_MAX_ARTICLES=50
export PAPERBOY_TOP_TAGS_LIMIT=20
exec $PYTHON ~/.hermes/skills/research/paperboy/scripts/paperboy.py
WRAPPER
chmod +x ~/.hermes/scripts/paperboy.sh

# Recycling cleanup wrapper
cat > ~/.hermes/scripts/cleanup-recycling.sh << WRAPPER
#!/bin/bash
# Recycling cleanup — delegates to the skill-owned Python script
exec $PYTHON ~/.hermes/skills/research/paperboy/scripts/cleanup-recycling.py
WRAPPER
chmod +x ~/.hermes/scripts/cleanup-recycling.sh

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
    RAW_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "paperboy"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
    if [ -n "$RAW_ID" ]; then
      hermes cron update "$RAW_ID" --no-agent --schedule "0 7 * * *" --deliver "$DELIVER" --name paperboy --script paperboy.sh
    fi
  }

echo "⏰ Creating cron job: paperboy-briefing (7:05 AM — radio + TTS)..."
hermes cron create \
  --name paperboy-briefing \
  --schedule "5 7 * * *" \
  --deliver "$DELIVER" \
  --skills paperboy \
  --prompt 'If the article data says "Sorry mate there'"'"'s no new news at the moment", just forward that message verbatim (no audio needed). STOP after that. Otherwise, pick a random celebrity persona and deliver a radio-style news briefing. Group articles by general topic (e.g. "Tech & AI", "Space", "Legal", "Deals & Sales", "Security", "Culture"), introducing each section with a short headline. For each article, embed its preview URL as a markdown link on the title and include at least 2 sentences of real summary. For the spoken TTS portion: only read the titles of articles that have Score: 0 — skip higher-scored articles in the audio. Send the transcript first, then generate TTS audio of the spoken portion and send the audio file.' 2>/dev/null || {
    echo "  ↳ Updating existing job instead..."
    BRIEFING_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "paperboy-briefing"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
    if [ -n "$BRIEFING_ID" ]; then
      hermes cron update "$BRIEFING_ID" --schedule "5 7 * * *" --deliver "$DELIVER" --name paperboy-briefing --skills paperboy --prompt 'If the article data says "Sorry mate there'"'"'s no new news at the moment", just forward that message verbatim (no audio needed). STOP after that. Otherwise, pick a random celebrity persona and deliver a radio-style news briefing. Group articles by general topic (e.g. "Tech & AI", "Space", "Legal", "Deals & Sales", "Security", "Culture"), introducing each section with a short headline. For each article, embed its preview URL as a markdown link on the title and include at least 2 sentences of real summary. For the spoken TTS portion: only read the titles of articles that have Score: 0 — skip higher-scored articles in the audio. Send the transcript first, then generate TTS audio of the spoken portion and send the audio file.'
    fi
  }

echo ""
echo "⛓️  Chaining context_from (primary relay — no file writing needed)..."
RAW_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "paperboy"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
BRIEFING_ID=$(hermes cron list 2>/dev/null | grep -B1 '"name": "paperboy-briefing"' | grep job_id | head -1 | sed 's/.*"\([^"]*\)".*/\1/')
if [ -n "$RAW_ID" ] && [ -n "$BRIEFING_ID" ]; then
  hermes cron update "$BRIEFING_ID" --context-from "$RAW_ID"
  echo "   Done! (paperboy-briefing receives paperboy stdout via context_from)"
fi

echo ""
echo "✅ Paperboy setup complete!"
echo ""
echo "📋 Cron jobs configured:"
echo "   7:00 AM — paperboy         (raw article list, no_agent mode)"
echo "   7:05 AM — paperboy-briefing (radio briefing + TTS audio, via context_from)"
echo ""
echo "🚀 Next run: Tomorrow at 7:00 AM (paperboy) + 7:05 AM (paperboy-briefing)"
