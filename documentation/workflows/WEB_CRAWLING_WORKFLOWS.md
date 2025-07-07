# Web Crawling Workflows

This document describes the web crawling workflows available in the Open Agentic Framework, demonstrating how to use the `WebScraperTool` for multi-step crawling and intelligent content extraction.

> **Note:**
> - The current workflows and agents support **multi-step (two-level) crawling**, not true recursive crawling. For recursive crawling (following links to arbitrary depth), you must implement custom logic or a Python agent.
> - With very small LLMs, the "intelligent" agent will not perform deep reasoning or advanced orchestration. It will return generic responses and cannot dynamically orchestrate recursive crawling.
> - All workflow JSON must use a `steps` array (not `workflow`), and each step must have a `type` field. Agents require `role`, `goals`, and `backstory` fields as strings.

## Overview

The framework provides a **Multi-Step + Agent Review** approach to web crawling:

1. **Multi-Step Web Crawling** - Crawl initial pages and extract links for further processing
2. **Agent Review and Analysis** - Use AI to review, analyze, and merge the crawled content
3. **Intelligent Decision Making** - Agent can assess quality, identify patterns, and make recommendations

## Limitations and Recursion

- **No true recursion:** The provided workflows and agents do not automatically recurse through new links found at each depth. They only perform a fixed number of steps (e.g., crawl initial page, then crawl extracted links).
- **How to enable recursion:** To perform recursive crawling, you must implement a custom agent or workflow with loop/recursion logic. This typically requires Python code or a workflow runner that supports iteration.
- **Agent/LLM limitations:** With small models (e.g., `smollm:135m`), agent responses will be generic and not capable of advanced orchestration or reasoning.

## Example: Recursive Crawling (Conceptual)

To implement true recursive crawling, you would need logic like this (pseudocode):

```json
{
  "steps": [
    {
      "step": 1,
      "name": "Crawl Pages",
      "type": "tool",
      "tool": "web_scraper",
      "parameters": {"urls": "{{current_urls}}", "extract_links": true, "link_filters": {"max_links": 10}},
      "output_key": "crawl_results"
    },
    {
      "step": 2,
      "name": "Check Depth",
      "type": "conditional",
      "condition": "{{current_depth < max_depth}}",
      "if_true": [
        {
          "type": "workflow",
          "workflow": "recursive_crawl",
          "parameters": {"current_urls": "{{crawl_results.extracted_links}}", "current_depth": "{{current_depth + 1}}"}
        }
      ]
    }
  ]
}
```
*This is conceptual; the current framework does not support workflow recursion/iteration out-of-the-box.*

## Prerequisites

Before running the web crawling workflows, ensure the framework is properly set up:

### 1. Start the Framework

```bash
# Navigate to the framework directory
cd agentic_ai_framework

# Start the framework with web UI
./start-web-ui.sh

# Or use Docker Compose directly
docker-compose up -d
```

### 2. Verify Services

```bash
# Check if services are running
docker-compose ps

# Verify API is responding
curl http://localhost:8000/health

# Check web UI
open http://localhost:8000/ui
```

### 3. Install Required Models

The workflows require LLM models for AI-powered analysis. Models are automatically downloaded, but you can check status:

```bash
# Check available models
curl http://localhost:11434/api/tags

# View model download progress
docker-compose logs model-setup
```

## Multi-Step Crawling with Agent Review

**Files**: 
- `samples/true_recursive_crawler.json` - True recursive crawler workflow that visits multiple pages

This workflow demonstrates the recommended pattern for web crawling: multi-step crawling followed by intelligent agent review and analysis.

### Workflow Steps

1. **Initial Site Crawl** - Crawl the initial site and extract relevant links
2. **Detailed Content Crawl** - Crawl the extracted links for detailed content
3. **Data Extraction and Structuring** - Extract and structure the crawled content
4. **Agent Review and Analysis** - Use AI agent to review, analyze, and merge the content
5. **Save Final Results** - Save the reviewed and analyzed results

### Key Features

- **Multi-step crawling** with controlled resource usage
- **Intelligent agent review** using ChatGPT-3.5-turbo or other LLMs
- **Quality assessment** and pattern recognition
- **Link filtering** and rate limiting
- **Data validation** and structuring

### Setup Instructions

#### 1. Create the Review Agent

```bash
# Create the agent via API
curl -X POST http://localhost:8000/agents \
  -H "Content-Type: application/json" \
  -d @samples/blog_title_analyzer.json

# Update to use ChatGPT-3.5-turbo (if available)
curl -X PUT http://localhost:8000/agents/web_crawling_review_agent \
  -H "Content-Type: application/json" \
  -d '{"ollama_model": "gpt-3.5-turbo"}'
```

#### 2. Create the Workflow

```bash
# Create the workflow via API
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d @samples/true_recursive_crawler.json
```

#### 3. Execute the Workflow

```bash
# Execute the workflow via API
curl -X POST "http://localhost:8000/workflows/Multi-Step%20Crawling%20with%20Agent%20Review/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "url": "https://quotes.toscrape.com/"
    }
  }'

# Or use the web UI at http://localhost:8000/ui
# Navigate to Workflows → Execute → Select workflow → Set parameters
```

### Test Results

This workflow has been tested and provides:

- **Controlled crawling** of 2-3 pages with rate limiting
- **Intelligent analysis** of crawled content quality and relevance
- **Pattern recognition** in quotes, authors, and themes
- **Quality assessment** with recommendations for further crawling
- **Memory efficient** operation suitable for laptops

### Configuration Options

- **URL**: The starting point for crawling
- **Link Filters**: Patterns to control which links to follow
- **Selectors**: CSS/XPath selectors for content extraction
- **Rate Limits**: Timing controls to be respectful to target sites
- **Agent Model**: Choose between small models (smollm:135m) or larger models (gpt-3.5-turbo)

## Configuration Options

### Rate Limiting

Both workflows support configurable rate limiting:

```json
{
  "rate_limit": {
    "requests_per_second": 1,
    "delay_between_requests": 2.0
  }
}
```

### Link Filtering

Control which links to follow:

```json
{
  "link_filters": {
    "include_patterns": ["/blog/", "/article/", "/news/"],
    "exclude_patterns": ["#", "javascript:", "mailto:"],
    "max_links": 10
  }
}
```

### Content Selectors

Define what content to extract:

```json
{
  "selectors": {
    "css": {
      "title": "h1, .title, .post-title",
      "content": ".content, .post-content, article",
      "author": ".author, .byline"
    }
  }
}
```

## Best Practices

### 1. Respect Rate Limits

Always configure appropriate rate limits to avoid overwhelming target websites:

```json
{
  "rate_limit": {
    "requests_per_second": 1,
    "delay_between_requests": 2.0
  }
}
```

### 2. Use Specific Selectors

Target specific content areas rather than extracting everything:

```json
{
  "selectors": {
    "css": {
      "main_content": "article .content, .post-body"
    }
  }
}
```

### 3. Implement Error Handling

Configure error handling to continue processing even if some pages fail:

```json
{
  "error_handling": {
    "continue_on_error": true,
    "max_retries": 3,
    "retry_delay": 5
  }
}
```

### 4. Choose Appropriate LLM Models

- **For memory-limited environments**: Use `smollm:135m` (91MB)
- **For better analysis**: Use `gpt-3.5-turbo` or larger models
- **For production**: Consider using OpenAI or other cloud providers

### 5. Validate Extracted Data

Use the `json_validator` tool to ensure data quality:

```json
{
  "tool": "json_validator",
  "parameters": {
    "action": "validate",
    "json_data": "{{extracted_data}}",
    "schema_type": "custom",
    "custom_schema": {
      "type": "object",
      "properties": {
        "title": {"type": "string"},
        "content": {"type": "string"}
      }
    }
  }
}
```

## Output Formats

The workflow produces structured output with agent analysis:

```json
{
  "agent_review": {
    "quality_analysis": "Assessment of content quality and relevance",
    "diversity_assessment": "Analysis of content diversity and patterns",
    "recommendations": "Suggestions for further crawling or analysis",
    "summary": "Overall assessment of the crawled content"
  },
  "final_results": {
    "filename": "crawling_review_results_2024-01-15T10:30:00Z.json",
    "status": "saved"
  }
}
```

## Troubleshooting

### Common Issues

1. **Rate Limiting**: If you encounter 429 errors, increase delays between requests
2. **Selector Issues**: If content isn't extracted, verify CSS selectors match the target site
3. **Link Filtering**: Adjust include/exclude patterns if too many or too few links are found
4. **Memory Usage**: For large sites, consider processing in batches
5. **Agent Model**: Ensure the agent is configured with an available LLM model

### Debug Mode

Enable debug logging to see detailed crawling information:

```bash
# View logs in real-time
docker-compose logs -f agentic-ai

# Or check specific service logs
docker-compose logs agentic-ai
```

## Integration with Other Tools

The web crawling workflows integrate seamlessly with other framework tools:

- **FileVaultTool**: Store crawled data for later use
- **DataExtractorTool**: Process and structure raw HTML content
- **JsonValidatorTool**: Validate extracted data quality
- **EmailSenderTool**: Send crawling results via email
- **HttpClientTool**: Make additional API calls for data enrichment

## Customization

The workflow can be customized for specific use cases:

1. **E-commerce Sites**: Focus on product information and pricing
2. **News Sites**: Extract articles, authors, and publication dates
3. **Documentation Sites**: Crawl API docs and tutorials
4. **Social Media**: Extract posts and user interactions (with appropriate permissions)

See the workflow files for complete configuration examples and modify them according to your specific needs. 

## Testing Agents Directly

While agents are often used as part of a workflow, you can also test them independently. This is useful for development, debugging, or evaluating agent behavior with custom input.

### 1. Test via API

You can execute an agent directly using a POST request to the agent's execute endpoint. For example, to test the `web_crawling_review_agent`:

```bash
curl -X POST http://localhost:8000/agents/web_crawling_review_agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Review and summarize the following crawled data.",
    "context": {
      "crawled_data": {
        "pages": [
          {"url": "https://quotes.toscrape.com/", "content": "Sample content from page 1"},
          {"url": "https://quotes.toscrape.com/page/2/", "content": "Sample content from page 2"}
        ]
      }
    }
  }'
```
- Replace the `task` and `context` with the data you want the agent to process.
- The response will contain the agent's analysis or summary.

### 2. Test via Web UI

1. Open your browser and go to [http://localhost:8000/ui](http://localhost:8000/ui).
2. Navigate to the **Agents** section.
3. Select the agent you want to test (e.g., `web_crawling_review_agent`).
4. Enter the task and context in the provided form.
5. Click **Execute** and review the output in the UI.

### 3. Test as Part of a Workflow

If your agent is part of a workflow (such as the multi-step crawling workflow), you can test the entire workflow, and the agent will be invoked as part of the process:

```bash
curl -X POST "http://localhost:8000/workflows/Multi-Step%20Crawling%20with%20Agent%20Review/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "url": "https://quotes.toscrape.com/"
    }
  }'
```

### 4. Debugging and Logs

- Check logs for agent execution details:
  ```bash
  docker-compose logs -f agentic-ai
  # or, if running locally:
  tail -f logs/agentic-ai.log
  ```

**Tip:** Use realistic sample data in the `context` to see how the agent handles real-world scenarios. Try different LLM models by updating the agent’s configuration for more advanced analysis. 