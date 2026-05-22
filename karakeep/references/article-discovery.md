# Automated Article Discovery Workflow for Karakeep

This reference document describes a workflow for automatically discovering articles based on your interests and adding them to Karakeep.

## Overview

The workflow uses a hybrid approach combining:
1. RSS/Feed monitoring via blogwatcher-cli
2. Tag-based analysis of favorited bookmarks
3. Learning framework to improve over time

## Key Commands Learned

### Getting JSON Output
Always use `--json` flag for machine-readable output:
```bash
karakeep --server-addr https://your-instance --json bookmarks search "is:fav"
```

### Searching Favorited Bookmarks
```bash
# Get all favorited bookmarks
karakeep --server-addr https://your-instance --json bookmarks search "is:fav"

# Get favorited bookmarks with specific tags
karakeep --server-addr https://your-instance --json bookmarks search "is:fav #AI #machine-learning"
```

### Adding Bookmarks via CLI
```bash
# Basic link addition
karakeep --server-addr https://your-instance bookmarks add --link "https://example.com"

# With tags
karakeep --server-addr https://your-instance bookmarks add --link "https://example.com" --tag-name "AI" --tag-name "research"

# With title and description (note)
karakeep --server-addr https://your-instance bookmarks add --link "https://example.com" --title "Article Title" --note "Brief description or summary"

# To a specific list
karakeep --server-addr https://your-instance bookmarks add --link "https://example.com" --list-id <list-id>
```

### Working with blogwatcher-cli
```bash
# Add a blog to track
blogwatcher-cli add "Blog Name" https://example.com/feed/

# Scan for new articles
blogwatcher-cli scan

# List unread articles
blogwatcher-cli articles

# List all tracked blogs
blogwatcher-cli blogs
```

## Discovery Strategies

### Strategy 1: RSS/Feed Monitoring
- Monitor blogs and news sites via RSS/Atom feeds
- Use blogwatcher-cli to track feeds and detect new articles
- Best for: Regularly updated content sources

### Strategy 2: Interest-Based Tag Analysis
- Analyze tags from your favorited bookmarks to determine interests
- Generate search queries based on top tags
- Best for: Discovering content related to your established interests

### Strategy 3: Learning Framework
- Track which discovered articles prove valuable
- Adjust tag weights and search strategies over time
- Best for: Personalized, improving recommendations

## Implementation Notes\\n\\n### JSON Parsing\\nWhen parsing Karakeep CLI output in scripts:\\n- Always use `--json` flag\\n- Handle potential JSON parsing errors\\n- Validate expected fields exist before accessing\\n\\n### RSS Feed Parsing\\nWhen extracting articles from blogwatcher-cli or similar RSS tools:\\n- Parse structured output to extract actual article titles, not generic placeholders\\n- Include rich metadata in descriptions: source, publication date, categories\\n- Use regex or line-by-line parsing for text output when JSON isn't available\\n- Validate and clean URLs (remove trailing punctuation)\\n\\n### Rate Limiting\\n- Be respectful when making external requests\\n- Add delays between API calls when doing web searches\\n- Respect robots.txt and terms of service\\n\\n### Deduplication\\n- **Always check for existing URLs before adding new bookmarks via CLI**\\n- Use `karakeep bookmarks search "url:<url>" --json` to check for duplicates\\n- Implement a function like `is_duplicate_url()` that returns True if URL exists\\n- Karakeep has built-in dedup for RSS imports, but CLI additions require manual checking\\n- Consider maintaining a local cache of recently added URLs for performance\\n\\n### Quality Over Quantity\\n- Implement scoring system to rank discovered articles\\n- Select only top N articles (e.g., top 10) for daily addition\\n- Base score on: RSS source (+10), tag matches (+1 per tag), learned preferences\\n- This ensures high-quality, relevant content rather than maximum volume\\n\\n### Learning Framework\\n- Track user interactions (favoriting, tagging) to improve future discoveries\\n- Adjust tag weights based on which articles users engage with\\n- Store learned data in JSON file for persistence across runs\\n- Allow the system to adapt to changing interests over time

## Example Workflow Script

See `~/.hermes/scripts/discover_articles_hybrid.py` for a complete implementation that:
1. Fetches favorited bookmarks
2. Extracts top interest tags
3. Discovers articles via RSS feeds
4. Discovers articles via tag-based search
5. Adds new articles to Karakeep with appropriate tags
6. Tracks learning data for future improvement

## Maintenance

### Updating Interests
The system automatically adapts to changing interests by:
- Regularly re-analyzing favorited bookmarks
- Weighting recent favorites more heavily
- Allowing manual override via learned tags

### Feed Management
Periodically review and update tracked blogs:
```bash
# Remove a blog
blogwatcher-cli remove "Blog Name" --yes

# List all blogs for review
blogwatcher-cli blogs
```

## Troubleshooting

### Authentication Issues
- Verify API key and server address
- Test with `karakeep whoami`
- Ensure environment variables are set correctly

### JSON Parsing Errors
- Confirm `--json` flag is used
- Check for unexpected output format
- Handle empty or malformed responses gracefully

### No New Articles Found
- Verify RSS feeds are active and accessible
- Check that blogwatcher-cli can access the feeds
- Consider adding more diverse feed sources