# Workflows

This section contains documentation for the various workflows available in the Open Agentic Framework.

## Available Workflows

### 1. [Email Reply Workflow](./EMAIL_REPLY_WORKFLOW.md)
A comprehensive workflow for processing email-based SBOM analysis requests, including data extraction, analysis, and automated email responses.

### 2. [SBOM Email Workflow](./SBOM_EMAIL_WORKFLOW.md)
Complete SBOM analysis workflow with email processing, license compliance analysis, and automated legal notices generation.

### 3. [Web Crawling Workflows](./WEB_CRAWLING_WORKFLOWS.md)
Multi-step web crawling workflows with intelligent agent review and analysis capabilities.

### 4. [Recursive Web Crawler Example](./RECURSIVE_WEB_CRAWLER_EXAMPLE.md)
A comprehensive example of a recursive web crawler that extracts blog post links and titles from ovalenzuela.com.

## Workflow Categories

### Email Processing
- **Email Reply Workflow**: Complete email-based SBOM analysis pipeline
  - Email parsing and data extraction
  - SBOM analysis and processing
  - Automated email response generation
  - File attachment handling

### Web Crawling
- **Multi-Step Crawling with Agent Review**: Intelligent web crawling with AI-powered analysis
  - Multi-step crawling with controlled resource usage
  - Agent review and quality assessment
  - Pattern recognition and content analysis
  - Rate limiting and respectful crawling
- **Recursive Blog Crawler**: Complete recursive crawling example
  - Starts with main site and discovers blog links
  - Follows links to individual blog posts
  - Extracts titles and metadata from each post
  - Creates comprehensive analysis reports

## Workflow Structure

All workflows in the framework follow a consistent structure:

```json
{
  "name": "Workflow Name",
  "description": "Workflow description",
  "steps": [
    {
      "step": 1,
      "name": "Step Name",
      "type": "tool|agent|workflow",
      "tool": "tool_name",
      "parameters": {
        "param1": "value1"
      },
      "output_key": "step_output"
    }
  ]
}
```

### Step Types

- **tool**: Execute a specific tool with parameters
- **agent**: Execute an AI agent with a task
- **workflow**: Execute a nested workflow

### Parameter Substitution

Workflows support parameter substitution using `{{variable_name}}` syntax:

```json
{
  "parameters": {
    "url": "{{input_url}}",
    "data": "{{previous_step_output}}"
  }
}
```

## Creating Custom Workflows

### 1. Define Workflow Structure

Create a JSON file with the required structure:

```json
{
  "name": "My Custom Workflow",
  "description": "Description of what this workflow does",
  "steps": [
    {
      "step": 1,
      "name": "Initial Step",
      "type": "tool",
      "tool": "web_scraper",
      "parameters": {
        "urls": "{{input_url}}"
      },
      "output_key": "scraped_data"
    }
  ]
}
```

### 2. Register the Workflow

```bash
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d @my_custom_workflow.json
```

### 3. Execute the Workflow

```bash
curl -X POST "http://localhost:8000/workflows/My%20Custom%20Workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "context": {
      "input_url": "https://example.com"
    }
  }'
```

## Best Practices

### 1. Error Handling

Include error handling in your workflows:

```json
{
  "step": 2,
  "name": "Error Handling",
  "type": "tool",
  "tool": "json_validator",
  "parameters": {
    "action": "validate",
    "json_data": "{{step1_output}}"
  },
  "on_error": {
    "action": "continue",
    "fallback_value": "{}"
  }
}
```

### 2. Data Validation

Validate data between steps:

```json
{
  "step": 3,
  "name": "Validate Data",
  "type": "tool",
  "tool": "json_validator",
  "parameters": {
    "action": "validate",
    "json_data": "{{processed_data}}",
    "schema_type": "custom",
    "custom_schema": {
      "type": "object",
      "required": ["title", "content"]
    }
  }
}
```

### 3. Resource Management

Use appropriate tools for resource management:

```json
{
  "step": 1,
  "name": "Rate Limited Request",
  "type": "tool",
  "tool": "rate_limiter",
  "parameters": {
    "action": "acquire",
    "resource": "api_calls",
    "max_requests": 10,
    "time_window": 60
  }
}
```

## Testing Workflows

### 1. Unit Testing

Test individual steps:

```bash
# Test a specific tool
curl -X POST http://localhost:8000/tools/web_scraper/execute \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com"]}'
```

### 2. Integration Testing

Test complete workflows:

```bash
# Execute workflow with test data
curl -X POST "http://localhost:8000/workflows/Test%20Workflow/execute" \
  -H "Content-Type: application/json" \
  -d @test_data.json
```

### 3. Monitoring

Monitor workflow execution:

```bash
# View workflow logs
docker-compose logs -f agentic-ai

# Check workflow status
curl http://localhost:8000/workflows
```

## Workflow Examples

### Sample Workflows

The `samples/` directory contains working workflow examples:

- `agentic_sbom_project.json` - Complete SBOM analysis workflow
- `true_recursive_crawler.json` - True recursive web crawler that visits multiple pages and extracts content from each
- `agentic_sbom_project.json` - Complete SBOM analysis workflow with email processing

### Customization

Modify the sample workflows to fit your specific needs:

1. **Change Parameters**: Update URLs, selectors, and configuration
2. **Add Steps**: Insert additional processing steps
3. **Modify Tools**: Use different tools for specific tasks
4. **Adjust Agents**: Configure agents with different models or prompts

## Troubleshooting

### Common Issues

1. **Step Dependencies**: Ensure previous steps complete before dependent steps
2. **Parameter Names**: Use exact parameter names as defined in tool documentation
3. **Data Types**: Ensure data types match tool expectations
4. **Resource Limits**: Monitor memory and CPU usage for large workflows

### Debug Mode

Enable debug logging:

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Restart services
docker-compose restart agentic-ai
```

## Integration

Workflows integrate with all framework components:

- **Tools**: Use any available tool in workflow steps
- **Agents**: Execute AI agents for complex decision making
- **Memory**: Store and retrieve data between workflow runs
- **File Vault**: Save results and intermediate data
- **Email Tools**: Send notifications and results

## Performance Optimization

### 1. Parallel Execution

Use parallel steps where possible:

```json
{
  "steps": [
    {
      "step": 1,
      "name": "Parallel Processing",
      "type": "parallel",
      "steps": [
        {"tool": "web_scraper", "parameters": {"urls": ["url1"]}},
        {"tool": "web_scraper", "parameters": {"urls": ["url2"]}}
      ]
    }
  ]
}
```

### 2. Caching

Cache expensive operations:

```json
{
  "step": 1,
  "name": "Cached Operation",
  "type": "tool",
  "tool": "file_vault",
  "parameters": {
    "action": "get",
    "key": "cached_data"
  },
  "fallback": {
    "tool": "expensive_operation",
    "parameters": {...}
  }
}
```

### 3. Resource Limits

Set appropriate resource limits:

```json
{
  "resource_limits": {
    "max_memory": "2GB",
    "max_cpu": "50%",
    "timeout": 300
  }
}
```

For detailed information about specific workflows, see the individual documentation files in this directory. 