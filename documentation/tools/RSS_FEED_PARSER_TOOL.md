# RSS Feed Parser Tool

## Overview

The RSS Feed Parser Tool is a generic tool for extracting structured data from RSS/Atom feeds. It supports both standard RSS/Atom formats and specialized feeds like Hacker News, providing comprehensive parsing capabilities with configurable options.

## Features

- **Multi-Format Support**: Handles RSS 2.0, RSS 1.0, and Atom feeds
- **Hacker News Integration**: Specialized parsing for Hacker News feeds with metadata extraction
- **Configurable Extraction**: Control number of items, content inclusion, and rate limiting
- **Error Handling**: Graceful handling of malformed feeds and network issues
- **Metadata Extraction**: Extracts feed metadata and item details

## Tool Configuration

### Basic Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `feed_urls` | array | required | List of RSS feed URLs to parse |
| `max_items` | integer | 10 | Maximum number of items to extract per feed |
| `include_content` | boolean | false | Whether to fetch full content |
| `rate_limit` | number | 1 | Delay between requests in seconds |

### Example Configuration

```json
{
  "feed_urls": [
    "https://hnrss.org/frontpage",
    "https://hnrss.org/frontpage?link=comments"
  ],
  "max_items": 15,
  "include_content": false,
  "rate_limit": 1
}
```

## Supported Feed Types

### Standard RSS/Atom Feeds

The tool can parse any standard RSS or Atom feed and extract:

- **Feed Metadata**: Title, description, link, language, updated date
- **Item Data**: Title, link, description, published date, author, tags
- **Content**: Full content if requested

### Hacker News Feeds

Specialized parsing for Hacker News feeds with additional metadata:

- **Points**: Article upvote count
- **Comment Count**: Number of comments
- **Comments URL**: Direct link to comment page
- **Article URL**: Original article URL
- **Author**: HN username

## Output Format

### Success Response

```json
{
  "success": true,
  "total_feeds": 2,
  "successful_feeds": 2,
  "failed_feeds": 0,
  "results": [
    {
      "feed_url": "https://hnrss.org/frontpage",
      "success": true,
      "feed_info": {
        "title": "Hacker News: Front Page",
        "description": "Hacker News RSS",
        "link": "https://news.ycombinator.com/",
        "language": "en",
        "updated": "Wed, 09 Jul 2025 06:38:18 +0000"
      },
      "items": [
        {
          "title": "Article Title",
          "link": "https://news.ycombinator.com/item?id=123456",
          "description": "Article description with metadata",
          "published": "Wed, 09 Jul 2025 05:49:52 +0000",
          "author": "username",
          "points": 30,
          "comment_count": 5,
          "comments_url": "https://news.ycombinator.com/item?id=123456",
          "article_url": "https://example.com/article"
        }
      ],
      "total_items": 15,
      "parsed_at": "2025-07-09T06:38:18.123456"
    }
  ],
  "message": "Parsed 2/2 feeds successfully"
}
```

### Error Response

```json
{
  "success": false,
  "total_feeds": 2,
  "successful_feeds": 1,
  "failed_feeds": 1,
  "results": [
    {
      "feed_url": "https://example.com/feed",
      "success": false,
      "error": "Network error: Connection timeout",
      "items": []
    }
  ],
  "message": "Parsed 1/2 feeds successfully"
}
```

## Usage Examples

### Basic RSS Parsing

```python
# Parse a single RSS feed
result = await rss_parser.execute({
    "feed_urls": ["https://example.com/feed.xml"],
    "max_items": 10
})
```

### Hacker News Analysis

```python
# Parse both main feed and comments feed
result = await rss_parser.execute({
    "feed_urls": [
        "https://hnrss.org/frontpage",
        "https://hnrss.org/frontpage?link=comments"
    ],
    "max_items": 20,
    "rate_limit": 1
})
```

### Content Extraction

```python
# Include full content for analysis
result = await rss_parser.execute({
    "feed_urls": ["https://blog.example.com/feed"],
    "max_items": 5,
    "include_content": true,
    "rate_limit": 2
})
```

## Error Handling

The tool implements comprehensive error handling:

- **Network Errors**: Timeouts, connection failures, HTTP errors
- **Parsing Errors**: Malformed XML, invalid RSS structure
- **Rate Limiting**: Configurable delays between requests
- **Partial Failures**: Continues processing other feeds if one fails

## Best Practices

### Rate Limiting

- Use appropriate rate limits to avoid overwhelming feed servers
- Default rate limit of 1 second is suitable for most feeds
- Increase rate limit for high-traffic feeds

### Content Management

- Only enable `include_content` when full content is needed
- Full content increases response size and processing time
- Consider using `max_items` to limit data volume

### Feed Validation

- Verify feed URLs before processing
- Check feed format compatibility
- Monitor for feed structure changes

## Integration with Workflows

The RSS Feed Parser Tool is designed to work seamlessly with other tools:

- **Data Extractor**: Extract specific fields from parsed results
- **File Vault**: Store parsed data for later analysis
- **JSON Validator**: Validate extracted data structure
- **AI Agents**: Provide structured data for analysis

## Security Considerations

- Validate feed URLs before processing
- Implement appropriate rate limiting
- Handle malformed XML safely
- Consider content sanitization for user-generated feeds

## Troubleshooting

### Common Issues

1. **Feed Not Found**: Verify URL and check if feed is accessible
2. **Parsing Errors**: Check feed format and XML validity
3. **Rate Limiting**: Increase rate limit if requests are blocked
4. **Content Issues**: Verify `include_content` parameter usage

### Debug Information

Enable logging to see detailed parsing information:

```python
import logging
logging.getLogger('tools.rss_feed_parser').setLevel(logging.DEBUG)
```

## Related Tools

- **Data Extractor**: Extract specific data from RSS results
- **Web Scraper**: Alternative for non-RSS content
- **HTTP Client**: Direct API access for custom feeds
- **File Vault**: Store and retrieve parsed feed data 