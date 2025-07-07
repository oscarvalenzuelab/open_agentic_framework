# Web Scraper Tool

The Web Scraper Tool is a powerful component of the Open Agentic Framework that enables intelligent web crawling and content extraction. It provides comprehensive web scraping capabilities with support for multiple URLs, CSS/XPath selectors, link extraction, rate limiting, and metadata extraction.

## Overview

The Web Scraper Tool is designed for:
- **Multi-URL Processing**: Scrape multiple URLs in a single operation
- **Intelligent Content Extraction**: Use CSS and XPath selectors to extract specific content
- **Link Discovery**: Automatically discover and filter links for recursive crawling
- **Rate Limiting**: Respectful crawling with configurable request rates
- **Metadata Extraction**: Extract page metadata including titles, descriptions, and Open Graph data
- **Error Handling**: Graceful handling of network errors and invalid responses

## Tool Configuration

### Basic Parameters

```json
{
  "urls": ["https://example.com", "https://example.org"],
  "selectors": {
    "css": {
      "title": "h1, .title, .post-title",
      "content": ".content, .post-content, article",
      "links": "a[href]"
    },
    "xpath": {
      "author": "//span[@class='author']",
      "date": "//time[@datetime]"
    }
  },
  "extract_links": true,
  "link_filters": {
    "include_patterns": ["/blog/", "/article/"],
    "exclude_patterns": ["#", "javascript:", "mailto:"],
    "same_domain_only": true
  },
  "rate_limit": {
    "requests_per_second": 1
  },
  "extract_metadata": true
}
```

### Parameter Details

#### `urls` (array, required)
List of URLs to scrape. Supports both HTTP and HTTPS.

```json
{
  "urls": [
    "https://example.com",
    "https://example.org/page1",
    "https://example.net/blog/post-1"
  ]
}
```

#### `selectors` (object, optional)
CSS and XPath selectors for content extraction.

**CSS Selectors:**
```json
{
  "css": {
    "page_title": "title",
    "content_title": "h1, .post-title, .article-title",
    "content": ".content, .post-content, article",
    "author": ".author, .byline",
    "date": ".date, .published-date, time",
    "tags": ".tags a, .categories a",
    "links": "a[href*='/blog'], a[href*='/post']"
  }
}
```

**XPath Selectors:**
```json
{
  "xpath": {
    "author": "//span[@class='author']",
    "date": "//time[@datetime]",
    "content": "//div[@class='content']",
    "links": "//a[contains(@href, '/blog')]"
  }
}
```

#### `extract_links` (boolean, optional)
Enable automatic link discovery and extraction.

```json
{
  "extract_links": true
}
```

#### `link_filters` (object, optional)
Configure link filtering for discovered links.

```json
{
  "link_filters": {
    "include_patterns": ["/blog/", "/post/", "/article/"],
    "exclude_patterns": ["#", "javascript:", "mailto:", "tel:"],
    "same_domain_only": true,
    "max_links": 50
  }
}
```

**Filter Options:**
- `include_patterns`: Array of patterns to include (regex)
- `exclude_patterns`: Array of patterns to exclude (regex)
- `same_domain_only`: Only include links from the same domain
- `max_links`: Maximum number of links to extract

#### `rate_limit` (object, optional)
Configure request rate limiting.

```json
{
  "rate_limit": {
    "requests_per_second": 1,
    "delay_between_requests": 1000
  }
}
```

#### `extract_metadata` (boolean, optional)
Extract page metadata including Open Graph and Twitter Card data.

```json
{
  "extract_metadata": true
}
```

## Usage Examples

### Basic Content Extraction

```json
{
  "urls": ["https://quotes.toscrape.com"],
  "selectors": {
    "css": {
      "quotes": ".quote .text",
      "authors": ".quote .author",
      "tags": ".quote .tag"
    }
  }
}
```

### Multi-Page Crawling with Link Discovery

```json
{
  "urls": ["https://example.com"],
  "selectors": {
    "css": {
      "blog_links": "a[href*='/blog'], a[href*='/post']",
      "content": ".content, article"
    }
  },
  "extract_links": true,
  "link_filters": {
    "include_patterns": ["/blog/", "/post/"],
    "exclude_patterns": ["#", "javascript:"],
    "same_domain_only": true
  },
  "rate_limit": {
    "requests_per_second": 1
  }
}
```

### Metadata Extraction

```json
{
  "urls": ["https://example.com"],
  "selectors": {
    "css": {
      "title": "title",
      "content": ".content"
    }
  },
  "extract_metadata": true
}
```

## Response Format

### Successful Response

```json
{
  "success": true,
  "total_urls": 2,
  "successful_scrapes": 2,
  "failed_scrapes": 0,
  "results": [
    {
      "url": "https://example.com",
      "success": true,
      "status_code": 200,
      "extracted_data": {
        "title": ["Example Page Title"],
        "content": ["Page content here..."],
        "author": ["John Doe"]
      },
      "metadata": {
        "title": "Example Page Title",
        "description": "Page description",
        "og_title": "Open Graph Title",
        "og_description": "Open Graph Description",
        "og_url": "https://example.com",
        "og_site_name": "Example Site",
        "og_type": "website",
        "twitter_card": "summary"
      },
      "links": [
        "https://example.com/blog/post-1",
        "https://example.com/blog/post-2"
      ],
      "content_length": 15420,
      "content_type": "text/html; charset=utf-8"
    }
  ],
  "errors": [],
  "discovered_links": [
    "https://example.com/blog/post-1",
    "https://example.com/blog/post-2"
  ],
  "message": "Scraped 2/2 URLs successfully"
}
```

### Error Response

```json
{
  "success": false,
  "total_urls": 1,
  "successful_scrapes": 0,
  "failed_scrapes": 1,
  "results": [],
  "errors": [
    {
      "url": "https://invalid-url.com",
      "error": "Connection timeout",
      "status_code": null
    }
  ],
  "discovered_links": [],
  "message": "Scraped 0/1 URLs successfully"
}
```

## Advanced Features

### Recursive Crawling

The Web Scraper Tool supports recursive crawling patterns when used in workflows:

```json
{
  "name": "recursive_crawler",
  "steps": [
    {
      "type": "tool",
      "name": "initial_scrape",
      "tool": "web_scraper",
      "parameters": {
        "urls": ["https://example.com"],
        "selectors": {
          "css": {
            "links": "a[href*='/blog']"
          }
        },
        "extract_links": true,
        "link_filters": {
          "include_patterns": ["/blog/"],
          "same_domain_only": true
        }
      }
    },
    {
      "type": "tool",
      "name": "recursive_scrape",
      "tool": "web_scraper",
      "parameters": {
        "urls": "{{initial_scrape.discovered_links}}",
        "selectors": {
          "css": {
            "title": "title",
            "content": ".content"
          }
        }
      }
    }
  ]
}
```

### Content Filtering

Use advanced selectors for precise content extraction:

```json
{
  "selectors": {
    "css": {
      "main_content": "main, .content, article",
      "navigation": "nav, .navigation, .menu",
      "footer": "footer, .footer",
      "sidebar": ".sidebar, aside",
      "comments": ".comments, .comment-section"
    },
    "xpath": {
      "structured_data": "//script[@type='application/ld+json']",
      "meta_tags": "//meta[@name='description']",
      "canonical": "//link[@rel='canonical']"
    }
  }
}
```

### Rate Limiting Strategies

Implement different rate limiting strategies:

**Conservative (1 request/second):**
```json
{
  "rate_limit": {
    "requests_per_second": 1
  }
}
```

**Moderate (2 requests/second):**
```json
{
  "rate_limit": {
    "requests_per_second": 2
  }
}
```

**Aggressive (5 requests/second):**
```json
{
  "rate_limit": {
    "requests_per_second": 5
  }
}
```

## Best Practices

### 1. Respect Rate Limits
Always implement appropriate rate limiting to avoid overwhelming servers:

```json
{
  "rate_limit": {
    "requests_per_second": 1
  }
}
```

### 2. Use Specific Selectors
Target specific content elements for better extraction:

```json
{
  "selectors": {
    "css": {
      "title": "h1, .post-title, .article-title",
      "content": ".content, .post-content, article",
      "author": ".author, .byline, .post-author"
    }
  }
}
```

### 3. Implement Link Filtering
Use link filters to control crawling scope:

```json
{
  "link_filters": {
    "include_patterns": ["/blog/", "/post/", "/article/"],
    "exclude_patterns": ["#", "javascript:", "mailto:", "tel:"],
    "same_domain_only": true
  }
}
```

### 4. Handle Errors Gracefully
Always check for errors in the response:

```json
{
  "success": true,
  "failed_scrapes": 0,
  "errors": []
}
```

### 5. Extract Metadata
Enable metadata extraction for additional context:

```json
{
  "extract_metadata": true
}
```

## Error Handling

### Common Error Types

1. **Connection Errors**: Network timeouts, DNS failures
2. **HTTP Errors**: 404, 500, 403 responses
3. **Parsing Errors**: Invalid HTML, encoding issues
4. **Rate Limiting**: Server-side rate limiting

### Error Response Structure

```json
{
  "errors": [
    {
      "url": "https://example.com",
      "error": "Connection timeout",
      "status_code": null
    },
    {
      "url": "https://example.com/404",
      "error": "HTTP 404 Not Found",
      "status_code": 404
    }
  ]
}
```

## Integration with Workflows

### Example: Blog Crawler Workflow

```json
{
  "name": "blog_crawler",
  "steps": [
    {
      "type": "tool",
      "name": "discover_links",
      "tool": "web_scraper",
      "parameters": {
        "urls": ["https://blog.example.com"],
        "selectors": {
          "css": {
            "blog_links": "a[href*='/blog'], a[href*='/post']"
          }
        },
        "extract_links": true,
        "link_filters": {
          "include_patterns": ["/blog/", "/post/"],
          "same_domain_only": true
        }
      }
    },
    {
      "type": "tool",
      "name": "extract_content",
      "tool": "web_scraper",
      "parameters": {
        "urls": "{{discover_links.discovered_links}}",
        "selectors": {
          "css": {
            "title": "title, h1",
            "content": ".content, .post-content",
            "author": ".author, .byline"
          }
        },
        "extract_metadata": true
      }
    }
  ]
}
```

## Performance Considerations

### Memory Usage
- Large HTML documents can consume significant memory
- Consider using `max_links` to limit link extraction
- Monitor response sizes for very large pages

### Network Efficiency
- Implement appropriate rate limiting
- Use `same_domain_only` to avoid external requests
- Consider caching responses for repeated requests

### Processing Time
- Multiple URLs increase processing time linearly
- Complex selectors may slow down parsing
- Rate limiting adds delays between requests

## Security Considerations

### Input Validation
- Validate URLs before processing
- Sanitize user-provided selectors
- Implement URL whitelisting if needed

### Rate Limiting
- Always implement rate limiting
- Respect robots.txt when available
- Use appropriate user agent strings

### Error Handling
- Don't expose sensitive information in error messages
- Log errors appropriately
- Implement retry logic for transient failures

## Troubleshooting

### Common Issues

1. **No Content Extracted**
   - Check if selectors match the page structure
   - Verify the page loads correctly
   - Check for JavaScript-rendered content

2. **Rate Limiting Issues**
   - Reduce `requests_per_second`
   - Implement exponential backoff
   - Check server response headers

3. **Link Discovery Problems**
   - Verify `extract_links` is enabled
   - Check link filter patterns
   - Ensure links are in the same domain

4. **Encoding Issues**
   - Check content-type headers
   - Verify HTML encoding
   - Handle special characters appropriately

### Debug Tips

1. **Test Selectors**: Use browser dev tools to test selectors
2. **Check Response**: Examine the full response structure
3. **Monitor Logs**: Check framework logs for detailed error information
4. **Start Small**: Test with single URLs before scaling up

The Web Scraper Tool provides a robust foundation for web crawling and content extraction, enabling sophisticated data collection and analysis workflows within the Open Agentic Framework. 