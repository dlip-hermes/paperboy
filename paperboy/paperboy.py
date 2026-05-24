#!/usr/bin/env python3
"""
Paperboy article discovery workflow for Karakeep.
Discovers recent articles based on favorited bookmarks and generates preview URLs.
Outputs the delivery title followed by styled title, summary, and preview URL for each article.
"""

import argparse
import json
import subprocess
import sys
import os
from datetime import datetime, timedelta


def run_karakeep_command_json(args):
    """Run a karakeep command and return parsed JSON output."""
    # Load environment variables from .env file
    env_path = os.path.expanduser('~/.hermes/.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value

    # Set the Karakeep environment variables
    subprocess_env = os.environ.copy()
    subprocess_env['KARAKEEP_SERVER_ADDR'] = env_vars.get('KARAKEEP_URL', 'https://karakeep.dex-lips.duckdns.org')
    subprocess_env['KARAKEEP_API_KEY'] = env_vars.get('KARAKEEP_API_KEY', '')

    cmd = ['npx', 'karakeep', '--server-addr', subprocess_env['KARAKEEP_SERVER_ADDR'], '--json'] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=subprocess_env)

    if result.returncode != 0:
        # Silently fail for cron job - no output to stderr
        return None

    # Handle empty output
    if not result.stdout.strip():
        # For some commands like update-tags, empty output might mean success
        return {'success': True}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        # If it's not JSON but command succeeded, return success
        if result.returncode == 0:
            return {'success': True}
        return None


def run_karakeep_command_raw(args):
    """Run a karakeep command and return raw output."""
    # Load environment variables from .env file
    env_path = os.path.expanduser('~/.hermes/.env')
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value

    # Set the Karakeep environment variables
    subprocess_env = os.environ.copy()
    subprocess_env['KARAKEEP_SERVER_ADDR'] = env_vars.get('KARAKEEP_URL', 'https://karakeep.dex-lips.duckdns.org')
    subprocess_env['KARAKEEP_API_KEY'] = env_vars.get('KARAKEEP_API_KEY', '')

    cmd = ['npx', 'karakeep', '--server-addr', subprocess_env['KARAKEEP_SERVER_ADDR']] + args
    result = subprocess.run(cmd, capture_output=True, text=True, env=subprocess_env)

    if result.returncode != 0:
        # Silently fail for cron job
        return None

    return result.stdout.strip()


def get_favorited_bookmarks():
    """Get all favorited bookmarks from Karakeep."""
    result = run_karakeep_command_json(["bookmarks", "search", "is:fav"])
    if result is None:
        return []
    # The karakeep search command returns an object with a 'bookmarks' key
    if isinstance(result, dict) and 'bookmarks' in result:
        return result.get("bookmarks", [])
    elif isinstance(result, dict) and result.get('success'):
        return []
    else:
        return []


def extract_tags_from_bookmarks(bookmarks):
    """Extract and count tags from favorited bookmarks."""
    all_tags = []
    for bm in bookmarks:
        if bm and isinstance(bm, dict):
            tags = bm.get('tags', [])
            all_tags.extend(tags)

    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    return tag_counts


def get_top_tags(tag_counts, limit=10, exclude=None):
    """Get top tags from favorited bookmarks with their counts."""
    if exclude is None:
        exclude = {'inbox'}

    # Filter out excluded tags
    filtered_tags = {tag: count for tag, count in tag_counts.items() if tag not in exclude}

    # Sort by count descending and return top limit
    sorted_tags = sorted(filtered_tags.items(), key=lambda x: x[1], reverse=True)
    return sorted_tags[:limit]


def get_last_run_time():
    """Get the last run time from strategy state file, converted to UTC.
    Returns a dict with 'full' (ISO timestamp) and 'date' (YYYY-MM-DD, 1 day earlier).
    The 'date' key is safe for Karakeep's after: filter (which only accepts YYYY-MM-DD),
    and the 'full' timestamp is used for client-side dedup.
    """
    home = os.path.expanduser('~')
    hermes_dir = os.path.join(home, '.hermes')
    article_discovery_dir = os.path.join(hermes_dir, '.paperboy')
    strategy_state_file = os.path.join(article_discovery_dir, "state.json")

    # Default: 48 hours ago in UTC (wider window for safety)
    import time
    if time.daylight and time.localtime().tm_isdst > 0:
        offset = time.altzone
    else:
        offset = time.timezone
    local_offset = timedelta(seconds=-offset)
    now_utc = datetime.now() - local_offset

    default_full = (now_utc - timedelta(hours=48)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
    default_date = (now_utc - timedelta(hours=48)).strftime('%Y-%m-%d')

    if os.path.exists(strategy_state_file):
        try:
            with open(strategy_state_file) as f:
                data = json.load(f)
                last_run = data.get('last_run')
                if last_run:
                    try:
                        # Parse stored time as local time, convert to UTC
                        local_dt = datetime.fromisoformat(last_run)
                        utc_dt = local_dt - local_offset
                        full = utc_dt.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        # Use date minus 1 day for a safe window
                        query_date = (utc_dt - timedelta(days=1)).strftime('%Y-%m-%d')
                        return {'full': full, 'date': query_date}
                    except Exception:
                        return {'full': last_run, 'date': default_date}
        except Exception:
            pass

    return {'full': default_full, 'date': default_date}

def save_last_run_time():
    """Save the current time as last run time."""
    home = os.path.expanduser('~')
    hermes_dir = os.path.join(home, '.hermes')
    article_discovery_dir = os.path.join(hermes_dir, '.paperboy')
    strategy_state_file = os.path.join(article_discovery_dir, "state.json")

    # Ensure directory exists
    os.makedirs(article_discovery_dir, exist_ok=True)

    data = {
        'last_run': datetime.now().isoformat(),
        'version': '2.0.0'
    }

    try:
        with open(strategy_state_file, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def get_new_articles_since(last_run_data):
    """Get bookmarks added since last_run_data['full'], using last_run_data['date'] for the after: query."""
    # Use YYYY-MM-DD format for the 'after:' filter (Karakeep only supports date format)
    query_date = last_run_data['date']
    full_timestamp = last_run_data['full']

    result = run_karakeep_command_json(["bookmarks", "search", f"after:{query_date}", "--limit", "100"])
    bookmarks = []
    if result and isinstance(result, dict):
        bookmarks = result.get("bookmarks", [])
    elif result and isinstance(result, dict) and result.get('success'):
        pass
    else:
        pass

    # Fallback: if after: query returned nothing, try without a time filter
    if not bookmarks:
        result = run_karakeep_command_json(["bookmarks", "search", "", "--limit", "100"])
        if result and isinstance(result, dict):
            bookmarks = result.get("bookmarks", [])
        elif result and isinstance(result, dict) and result.get('success'):
            pass
        else:
            pass

    # Filter client-side using the full timestamp for precision
    valid_bookmarks = []
    for bm in bookmarks:
        if bm and isinstance(bm, dict):
            created = bm.get('createdAt', '')
            if created and isinstance(created, str) and created.endswith('Z'):
                if created > full_timestamp:
                    valid_bookmarks.append(bm)
            else:
                valid_bookmarks.append(bm)

    return valid_bookmarks


def score_article(article, top_tags):
    """Score an article based on tag relevance from favorited bookmarks."""
    # Ensure article is a dict and has the necessary fields
    if not article or not isinstance(article, dict):
        return 0

    score = 0
    article_tags = [tag.lower().strip() for tag in article.get('tags', []) if tag.strip()]
    title_lower = (article.get('title') or '').lower()

    # Build normalized tag weights: count / max_count so top tag = 1.0
    if top_tags:
        max_count = top_tags[0][1] if top_tags else 1
        tag_weights = {tag: count / max_count for tag, count in top_tags}
    else:
        tag_weights = {}

    # Score based on tag matches
    for interest_tag, weight in tag_weights.items():
        interest_lower = interest_tag.lower()

        # Check if interest tag matches any article tag
        for article_tag in article_tags:
            if interest_lower in article_tag or article_tag in interest_lower:
                score += int(3 * weight)
                break

            # Also check for word overlap (for multi-word tags)
            interest_words = set(interest_lower.split())
            article_words = set(article_tag.split())
            if len(interest_words & article_words) >= min(2, len(interest_words)):
                score += int(3 * weight)
                break

        # Check title for keyword matches
        interest_words = interest_lower.split()
        if len(interest_words) >= 2 and all(w in title_lower for w in interest_words):
            score += int(2 * weight)
        elif len(interest_words) == 1 and interest_lower in title_lower:
            score += int(2 * weight)

    return score


def main():
    """Main function to discover and output article info for recent articles."""
    # Parse CLI args
    parser = argparse.ArgumentParser(description='Paperboy article discovery')
    parser.add_argument('--output-file', '-o', type=str, default=None,
                        help='Write output to this file in addition to stdout')
    args, _ = parser.parse_known_args()

    # Collect output in a buffer
    output_lines = []

    # Get favorited bookmarks to determine interests
    favorited = get_favorited_bookmarks()
    if not favorited:
        flush_output(output_lines, output_file=args.output_file)
        return 1

    # Extract and count tags
    tag_counts = extract_tags_from_bookmarks(favorited)
    top_tags = get_top_tags(tag_counts, limit=int(os.environ.get('PAPERBOY_TOP_TAGS_LIMIT', '8')))

    # Get last run time (returns dict with 'full' and 'date' keys)
    last_run_data = get_last_run_time()

    # Get new articles since last run
    new_articles = get_new_articles_since(last_run_data)
    if not new_articles:
        # Still update last run time to avoid checking same period next time
        save_last_run_time()
        # Output friendly no-news message
        output_lines.append("# 🗞️🏃💨 Paperboy Run!")
        output_lines.append("")
        output_lines.append("Sorry mate there's no new news at the moment")
        flush_output(output_lines, output_file=args.output_file)
        return 0

    # Score articles
    scored_articles = []
    for article in new_articles:
        # Skip invalid articles
        if not article or not isinstance(article, dict):
            continue
        score = score_article(article, top_tags)
        scored_articles.append({'article': article, 'score': score})

    # Sort by score descending
    scored_articles.sort(key=lambda x: x['score'], reverse=True)

    # Take top N articles (default 10, overridable via PAPERBOY_MAX_ARTICLES env var)
    # Use -1 for no limit
    MAX_ARTICLES = int(os.environ.get('PAPERBOY_MAX_ARTICLES', '10'))
    if MAX_ARTICLES == -1:
        top_articles = scored_articles
    else:
        top_articles = scored_articles[:MAX_ARTICLES]

    # Generate article info for selected articles
    articles_info = []
    for item in top_articles:
        article = item["article"]
        if article and isinstance(article, dict):
            # Get title - check content.title if main title is missing/null
            title = article.get('title')
            if not title and article.get('content') and isinstance(article.get('content'), dict):
                title = article.get('content', {}).get('title')
            title = title or 'No title'
            
            # Get summary - check content.description if main summary is missing
            summary = article.get('summary') or article.get('description', '')
            if not summary and article.get('content') and isinstance(article.get('content'), dict):
                summary = article.get('content', {}).get('description', '')
            summary = summary or ''
            
            bookmark_id = article.get("id")
            if bookmark_id:
                preview_url = f"https://karakeep.dex-lips.duckdns.org/dashboard/preview/{bookmark_id}"
                articles_info.append({
                    'title': title,
                    'summary': summary,
                    'url': preview_url,
                    'score': item['score']
                })

    # Update last run time
    save_last_run_time()

    # Output the title first as H1, then for each article: title as H2, summary, URL
    output_lines.append("# 🏃💨 Paperboy Run! 🗞️")
    output_lines.append("")  # Empty line after title
    for i, info in enumerate(articles_info):
        output_lines.append(f"## [{info['title']}]({info['url']})")
        output_lines.append("")  # Blank line between fields
        if info['score'] > 0:
            output_lines.append(f"{info['summary']}")
            output_lines.append("")  # Blank line between fields
        output_lines.append(f"Score: {info['score']}")
        # Add a blank line between articles except after the last one
        if i < len(articles_info) - 1:
            output_lines.append("")  # Only one blank line between articles

    flush_output(output_lines, output_file=args.output_file)
    return 0


def flush_output(lines, output_file=None):
    """Print lines to stdout and optionally write to a file."""
    text = '\n'.join(lines)
    sys.stdout.write(text)
    sys.stdout.write('\n')
    sys.stdout.flush()
    if output_file:
        try:
            os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(text)
                f.write('\n')
        except Exception:
            pass


if __name__ == "__main__":
    exit(main())