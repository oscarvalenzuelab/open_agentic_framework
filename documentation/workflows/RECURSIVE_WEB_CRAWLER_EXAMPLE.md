# Recursive Web Crawler Example

This document demonstrates how to create a recursive web crawler using the Open Agentic Framework that can crawl a website, extract blog post links, and extract titles from each post.

## Overview

The example crawler will:
1. Start with the main website (https://ovalenzuela.com)
2. Extract all blog post links from the main page
3. Visit each blog post URL
4. Extract the title from each blog post page
5. Compile a comprehensive report of all blog posts and their titles

## True Recursive Crawler Workflow

This workflow demonstrates **true recursive crawling** by visiting each individual blog post page and extracting the HTML `<title>` tag:

```json
{
  "name": "true_recursive_blog_crawler",
  "description": "True recursive web crawler that visits each blog post page and extracts HTML title tags",
  "steps": [
    {
      "type": "tool",
      "name": "web_scraper",
      "tool": "web_scraper",
      "parameters": {
        "urls": ["https://ovalenzuela.com"],
        "selectors": {
          "css": {
            "blog_links": "a[href*='/blog'], a[href*='/post'], a[href*='/article'], .post-link a, .blog-post a"
          }
        },
        "extract_links": true,
        "link_filters": {
          "include_patterns": ["/blog/", "/post/", "/article/"],
          "exclude_patterns": ["#", "javascript:", "mailto:", "tel:"],
          "same_domain_only": true
        },
        "rate_limit": {
          "requests_per_second": 1
        }
      }
    },
    {
      "type": "tool",
      "name": "data_extractor",
      "tool": "data_extractor",
      "parameters": {
        "source_data": "{{web_scraper}}",
        "extractions": [
          {
            "name": "blog_urls",
            "type": "path",
            "query": "discovered_links"
          }
        ]
      }
    },
    {
      "type": "tool",
      "name": "web_scraper_posts",
      "tool": "web_scraper",
      "parameters": {
        "urls": "{{data_extractor.blog_urls}}",
        "selectors": {
          "css": {
            "page_title": "title",
            "content_title": "h1, .post-title, .article-title, .title"
          }
        },
        "extract_metadata": true,
        "rate_limit": {
          "requests_per_second": 1
        }
      }
    },
    {
      "type": "tool",
      "name": "data_extractor_titles",
      "tool": "data_extractor",
      "parameters": {
        "source_data": "{{web_scraper_posts}}",
        "extractions": [
          {
            "name": "page_titles",
            "type": "find",
            "find_criteria": {
              "array_path": "results",
              "match_field": "success",
              "match_value": "true",
              "extract_field": "extracted_data"
            }
          },
          {
            "name": "page_urls",
            "type": "find",
            "find_criteria": {
              "array_path": "results",
              "match_field": "success",
              "match_value": "true",
              "extract_field": "url"
            }
          }
        ]
      }
    },
    {
      "type": "agent",
      "name": "blog_title_analyzer",
      "parameters": {
        "task": "Analyze the crawled blog post pages from ovalenzuela.com. For each blog post page that was successfully crawled, extract the HTML title tag and content title. Create a comprehensive report that includes: 1) Total number of blog post pages visited, 2) List of all blog posts with their URLs and HTML titles, 3) Analysis of the content themes and topics, 4) Any patterns in the blog structure. Structure the output as a clear, organized report with each blog post listed with its URL and title."
      }
    },
    {
      "type": "tool",
      "name": "file_vault",
      "tool": "file_vault",
      "parameters": {
        "action": "write",
        "filename": "blog_page_titles_{{timestamp}}.json",
        "content": "{{blog_title_analyzer}}",
        "overwrite": true
      }
    }
  ]
}
```

## Simple Blog Crawler Workflow

For sites where blog links are not easily discoverable, this simpler workflow extracts titles from the main page:

```json
{
  "name": "simple_blog_crawler",
  "description": "Simple web crawler that extracts blog post titles from ovalenzuela.com",
  "steps": [
    {
      "type": "tool",
      "name": "web_scraper",
      "tool": "web_scraper",
      "parameters": {
        "urls": ["https://ovalenzuela.com"],
        "selectors": {
          "css": {
            "blog_titles": "h2, h3, .post-title, .article-title, .title",
            "blog_links": "a[href*='/blog'], a[href*='/post'], a[href*='/article']",
            "main_content": "main, .content, article, body"
          }
        },
        "extract_links": true,
        "link_filters": {
          "include_patterns": ["/blog/", "/post/", "/article/"],
          "exclude_patterns": ["#", "javascript:", "mailto:", "tel:"],
          "same_domain_only": true
        },
        "rate_limit": {
          "requests_per_second": 1
        }
      }
    },
    {
      "type": "tool",
      "name": "data_extractor",
      "tool": "data_extractor",
      "parameters": {
        "source_data": "{{web_scraper}}",
        "extractions": [
          {
            "name": "blog_post_titles",
            "type": "path",
            "query": "results[0].extracted_data.blog_titles"
          }
        ]
      }
    },
    {
      "type": "tool",
      "name": "file_vault",
      "tool": "file_vault",
      "parameters": {
        "action": "write",
        "filename": "blog_titles_{{timestamp}}.json",
        "content": "{{data_extractor}}",
        "overwrite": true
      }
    }
  ]
}
```

## Agent Configuration

```json
{
  "name": "blog_title_analyzer",
  "description": "Specialized agent for analyzing blog page titles and HTML metadata from crawled pages",
  "role": "Blog Page Title Analyst",
  "goals": "Extract and analyze HTML title tags from blog post pages; identify patterns in page titles and metadata; create comprehensive reports of blog page structure and content.",
  "backstory": "You are an expert web analyst specializing in blog page analysis and HTML metadata extraction. You have extensive experience in analyzing page titles, HTML structure, and identifying patterns in blog content organization.",
  "ollama_model": "smollm:135m",
  "tools": [
    "data_extractor",
    "file_vault",
    "json_validator"
  ],
  "system_prompt": "You are a specialized blog page title analyst focused on extracting and analyzing HTML title tags from blog posts. Your expertise includes:\n\n1. **HTML Title Extraction**: Identifying and extracting title tags from HTML pages\n2. **Page Analysis**: Analyzing page structure and metadata\n3. **Content Pattern Recognition**: Identifying themes and patterns in blog titles\n4. **Report Generation**: Creating structured reports of blog page analysis\n\nWhen analyzing blog page data:\n- Focus on extracting clear, accurate HTML titles\n- Identify patterns in title structure and content\n- Provide structured, well-organized output\n- Include URLs and metadata when available\n- Create comprehensive summaries\n\nAlways provide clear, structured analysis with specific sections for different aspects of the blog page content.",
  "temperature": 0.3,
  "max_tokens": 4000
}
```

## Step-by-Step Explanation

### True Recursive Crawler Steps:

#### Step 1: Initial Site Crawl
- **Tool**: `web_scraper`
- **Purpose**: Crawl the main website to discover blog post links
- **Configuration**:
  - Targets https://ovalenzuela.com
  - Uses CSS selectors to find blog post links
  - Enables link extraction with filters for blog-related URLs
  - Implements rate limiting to be respectful to the server

#### Step 2: Extract Blog URLs
- **Tool**: `data_extractor`
- **Purpose**: Extract the discovered blog post URLs for further processing
- **Configuration**:
  - Uses path query to extract discovered_links
  - Prepares clean URL list for recursive crawling

#### Step 3: Crawl Individual Blog Posts
- **Tool**: `web_scraper`
- **Purpose**: Visit each blog post URL and extract content
- **Configuration**:
  - Uses the extracted blog URLs as input
  - Targets HTML `<title>` tags and content titles
  - Extracts metadata for additional context
  - **This is the recursive part** - visits each individual page

#### Step 4: Extract Page Titles
- **Tool**: `data_extractor`
- **Purpose**: Process the crawled blog posts to extract structured data
- **Configuration**:
  - Filters successful scrapes
  - Extracts both page titles and URLs for analysis

#### Step 5: Blog Analysis
- **Agent**: `blog_title_analyzer`
- **Purpose**: Analyze the extracted blog data and create a comprehensive report
- **Configuration**:
  - Specialized agent for blog page analysis
  - Creates structured reports with URLs and HTML titles

#### Step 6: Save Report
- **Tool**: `file_vault`
- **Purpose**: Save the analysis results to a file for later review
- **Configuration**:
  - Creates timestamped JSON file
  - Includes full analysis results

## Usage Example

### Register the Agent
```bash
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d @blog_title_analyzer.json
```

### Register the Workflow
```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d @true_recursive_blog_crawler.json
```

### Execute the Workflow
```bash
curl -X POST http://localhost:8000/workflows/true_recursive_blog_crawler/execute \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Expected Output

The true recursive workflow will produce a comprehensive report including:

```json
{
  "blog_analysis": {
    "total_pages_visited": 6,
    "successful_crawls": 5,
    "failed_crawls": 1,
    "blog_posts": [
      {
        "url": "https://ovalenzuela.com/blog/ai-agents-sbom-compliance",
        "html_title": "AI Agents: The Missing Piece in SBOM Compliance | Oscar's Blog",
        "content_title": "AI Agents: The Missing Piece in SBOM Compliance",
        "date": "2024-01-15",
        "author": "Oscar Valenzuela"
      },
      {
        "url": "https://ovalenzuela.com/blog/why-sboms-fail",
        "html_title": "Why Most SBOMs Fail and What to Do About It | Oscar's Blog",
        "content_title": "Why Most SBOMs Fail and What to Do About It",
        "date": "2024-01-20",
        "author": "Oscar Valenzuela"
      }
    ],
    "content_themes": [
      "Software Development",
      "AI and Machine Learning", 
      "Open Source Projects",
      "Technical Tutorials"
    ],
    "analysis": "The blog focuses primarily on technical content related to software development and AI frameworks..."
  }
}
```

## Key Features

### True Recursive Crawling
- Starts with main site and discovers blog links
- **Visits each individual blog post page**
- **Extracts HTML `<title>` tags from each page**
- Creates comprehensive analysis of all pages

### Intelligent Content Extraction
- Uses CSS selectors to target specific content elements
- Extracts both HTML titles and content titles
- Handles different HTML structures and layouts
- Implements rate limiting (1 request/second)

### Comprehensive Analysis
- Specialized blog page analysis agent
- Extracts titles, URLs, and metadata
- Identifies content themes and patterns
- Creates structured, searchable reports

### Rate Limiting and Respect
- Implements 1 request per second rate limiting
- Respects robots.txt and server resources
- Uses appropriate user agent strings

### Error Handling
- Tracks successful and failed crawls
- Continues processing even if some pages fail
- Provides detailed error reporting

### Structured Output
- Creates organized, searchable reports
- Includes metadata and analysis
- Saves results for later review

## Customization Options

### Target Different Sites
Change the initial URL and adjust selectors:
```json
{
  "urls": ["https://your-target-site.com"],
  "selectors": {
    "css": {
      "blog_links": "a[href*='/blog'], .post-link a, .article-link a"
    }
  }
}
```

### Extract Different Content
Modify selectors to extract different content types:
```json
{
  "selectors": {
    "css": {
      "page_title": "title",
      "content_title": "h1, .post-title, .article-title",
      "tags": ".tags a, .categories a",
      "comments": ".comments, .comment-section"
    }
  }
}
```

### Adjust Crawling Depth
Modify link filters to control crawling scope:
```json
{
  "link_filters": {
    "include_patterns": ["/blog/", "/post/", "/article/"],
    "exclude_patterns": ["#", "javascript:", "external"],
    "max_links": 20,
    "same_domain_only": true
  }
}
```

## Best Practices

1. **Respect Rate Limits**: Always implement appropriate rate limiting
2. **Handle Errors Gracefully**: Continue processing even if some pages fail
3. **Use Specific Selectors**: Target specific content elements for better extraction
4. **Validate Data**: Use data extraction tools to validate and clean results
5. **Save Results**: Always save results for later analysis and review
6. **Monitor Performance**: Track success rates and processing times
7. **Respect Robots.txt**: Check and respect website crawling policies

## Limitations

- **Template Substitution**: Complex template substitutions may not work reliably
- **Link Discovery**: Some sites may not have easily discoverable blog links
- **Rate Limiting**: True recursive crawling requires careful rate limiting
- **Error Handling**: Individual page failures can affect overall results

This example demonstrates a complete recursive web crawling solution that can be adapted for various websites and content types while maintaining good crawling practices and producing structured, actionable results. 