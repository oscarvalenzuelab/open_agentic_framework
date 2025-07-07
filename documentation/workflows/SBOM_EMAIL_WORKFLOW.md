# SBOM Email Workflow

The SBOM Email Workflow is a comprehensive automated system that processes Software Bill of Materials (SBOM) files received via email, analyzes license compliance, and generates detailed legal notices and risk assessments. This workflow demonstrates the framework's ability to handle complex multi-step processes involving email processing, file analysis, and automated reporting.

## Overview

The SBOM Email Workflow automates the entire process of:
1. **Email Monitoring**: Checking for new emails with SBOM attachments
2. **File Processing**: Extracting and parsing SBOM data
3. **License Analysis**: Analyzing each package for license compliance
4. **Risk Assessment**: Generating comprehensive risk reports
5. **Legal Documentation**: Creating legal notices for compliance
6. **Response Generation**: Sending automated email responses with results

## Workflow Structure

### Workflow Name: `email_test_workflow_no_agent`

```json
{
  "name": "email_test_workflow_no_agent",
  "description": "Test email checker with tool-level configuration and automatic reply",
  "steps": [
    // Email checking and processing
    // SBOM data extraction
    // License analysis
    // Legal notices generation
    // Email response
  ]
}
```

## Step-by-Step Process

### Step 1: Email Checking
**Tool**: `email_checker`
**Purpose**: Monitor inbox for new emails with SBOM attachments

```json
{
  "type": "tool",
  "name": "email_checker",
  "tool": "email_checker",
  "parameters": {
    "action": "check_emails",
    "protocol": "imap",
    "folder": "INBOX",
    "unread_only": true,
    "include_attachments": false,
    "limit": 1
  }
}
```

**Configuration**:
- **Protocol**: IMAP for email server connection
- **Folder**: INBOX (can be customized)
- **Unread Only**: Processes only unread emails
- **Limit**: 1 email per execution (configurable)
- **Attachments**: Initially disabled for performance

### Step 2: Email Content Reading
**Tool**: `email_checker`
**Purpose**: Read the full content of discovered emails

```json
{
  "type": "tool",
  "name": "email_checker",
  "tool": "email_checker",
  "parameters": {
    "action": "read_email",
    "email_id": "1",
    "unread_only": true,
    "limit": 2
  }
}
```

**Features**:
- Reads email body and metadata
- Extracts sender information
- Identifies attachment types
- Preserves email structure

### Step 3: Email Data Conversion
**Tool**: `email_data_converter`
**Purpose**: Convert email data to structured format

```json
{
  "type": "tool",
  "name": "email_data_converter",
  "tool": "email_data_converter",
  "parameters": {
    "email_data": "{{email_content}}",
    "action": "convert_to_object"
  }
}
```

**Processing**:
- Converts email to structured JSON
- Extracts sender information
- Normalizes email data format
- Prepares for attachment processing

### Step 4: Sender Information Extraction
**Tool**: `email_data_converter`
**Purpose**: Extract sender details for response

```json
{
  "type": "tool",
  "name": "email_data_converter",
  "tool": "email_data_converter",
  "parameters": {
    "email_data": "{{email_content}}",
    "action": "extract_sender"
  }
}
```

**Extracted Data**:
- Sender email address
- Sender name
- Reply-to information
- Email headers

### Step 5: Attachment Download
**Tool**: `email_attachment_downloader`
**Purpose**: Download and process SBOM attachments

```json
{
  "type": "tool",
  "name": "email_attachment_downloader",
  "tool": "email_attachment_downloader",
  "parameters": {
    "email_data": "{{converted_email_data.result}}",
    "download_path": "/tmp/email_attachments",
    "store_in_vault": true
  }
}
```

**Features**:
- Downloads all email attachments
- Stores files in secure vault
- Supports multiple file formats
- Preserves file metadata

### Step 6: File Content Reading
**Tool**: `file_vault`
**Purpose**: Read downloaded SBOM file content

```json
{
  "type": "tool",
  "name": "file_vault",
  "tool": "file_vault",
  "parameters": {
    "action": "read",
    "filename": "{{attachments.vault_files[0].vault_filename}}",
    "vault_id": "{{attachments.vault_id}}"
  }
}
```

**Processing**:
- Reads SBOM file content
- Supports JSON, XML, and text formats
- Handles large file sizes
- Preserves file encoding

### Step 7: PURL Extraction
**Tool**: `data_extractor`
**Purpose**: Extract Package URLs (PURLs) from SBOM data

```json
{
  "type": "tool",
  "name": "data_extractor",
  "tool": "data_extractor",
  "parameters": {
    "source_data": "{{vault_file_content.content}}",
    "extractions": [
      {
        "name": "purls",
        "type": "join_field",
        "query": "components",
        "field": "purl",
        "separator": ",",
        "default": ""
      }
    ]
  }
}
```

**Extraction Logic**:
- Parses SBOM structure
- Extracts all PURLs from components
- Joins PURLs into comma-separated list
- Handles various SBOM formats

### Step 8: License Analysis
**Agent**: `purl_batch_processor`
**Purpose**: Process PURLs and generate license risk assessment

```json
{
  "type": "agent",
  "name": "purl_batch_processor",
  "parameters": {
    "task": "Process the following list of PURLs and generate a license risk report.\n\nPURLs to process: {{extracted_purls.extracted_data.purls}}.\n\nProcess each PURL and consolidate results into a single output with the following structure:\n\n{\n  \"EXECUTIVE SUMMARY\": {\n    \"overall_risk_level\": \"CRITICAL/HIGH/MEDIUM/LOW\",\n    \"total_packages_analyzed\": <number>,\n    \"key_findings\": [\"finding1\", \"finding2\", ...],\n    \"summary\": \"Overall assessment summary\"\n  },\n  \"INDIVIDUAL ASSESSMENTS\": {\n    \"<purl1>\": {license_result1}, {legal_notices1},\n    \"<purl2>\": {license_result2}, {legal_notices2},\n    ...\n  },\n  \"PATTERN ANALYSIS\": {\n    \"common_license_types\": [\"MIT\", \"Apache-2.0\", ...]\n  },\n  \"AGGREGATE STATISTICS\": {\n    \"total_packages\": <number>,\n    \"high_risk_count\": <number>,\n    \"medium_risk_count\": <number>,\n    \"low_risk_count\": <number>,\n    \"license_distribution\": {\"MIT\": <count>, \"Apache-2.0\": <count>, ...}\n  }\n}"
  }
}
```

**Analysis Features**:
- **Risk Assessment**: Categorizes packages by risk level
- **License Analysis**: Identifies license types and compliance
- **Pattern Recognition**: Finds common license patterns
- **Statistical Analysis**: Provides aggregate statistics
- **Executive Summary**: High-level risk overview

### Step 9: Legal Notices Generation
**Agent**: `OSS_Legal_Notices_Generator`
**Purpose**: Generate legal notices document

```json
{
  "type": "agent",
  "name": "OSS_Legal_Notices_Generator",
  "parameters": {
    "task": "Produce a Legal Notices document for the information {{sbom_license_information}}"
  }
}
```

**Document Generation**:
- Creates comprehensive legal notices
- Includes all required attributions
- Formats for compliance requirements
- Provides copyright information

### Step 10: Email Response
**Tool**: `email_sender`
**Purpose**: Send automated response with analysis results

```json
{
  "type": "tool",
  "name": "email_sender",
  "tool": "email_sender",
  "parameters": {
    "to": "{{sender_info.result}}",
    "subject": "Re: test SBOM - SBOM Analysis Complete",
    "body": "Your SBOM analysis has been completed successfully.\n\nPlease find the legal notices and license assessment attached.\n\nWorkflow Results:\n{{legal_notices}}\n\nThis analysis was performed automatically by the Agentic AI Framework.\n\nBest regards,\nSBOM Analysis System",
    "html": false,
    "attachments": [
      {
        "filename": "legal_notices.txt",
        "content": "{{legal_notices}}",
        "content_type": "text/plain"
      }
    ]
  }
}
```

**Response Features**:
- **Automated Reply**: Sends response to original sender
- **Analysis Summary**: Includes key findings
- **Legal Notices**: Attaches generated legal document
- **Professional Format**: Maintains professional communication

## Agent Configuration

### PURL Batch Processor Agent

```json
{
  "name": "purl_batch_processor",
  "role": "PURL Batch Processor",
  "goals": "Execute the purl_license_and_notices workflow and consolidate the results into a single output.",
  "backstory": "You are a specialized tool agent that executes agentic workflows to obtain information from PURLs. You will receive one or multiple PURLS, and you will execute the http_client tool for each to obtain information about Licenses and Copyright statements.",
  "tools": ["http_client"],
  "ollama_model": "gpt-3.5-turbo"
}
```

**Capabilities**:
- Processes multiple PURLs in batch
- Calls external license databases
- Consolidates results into structured reports
- Handles various package types (npm, pypi, maven, etc.)

### OSS Legal Notices Generator Agent

```json
{
  "name": "OSS_Legal_Notices_Generator",
  "role": "OSS Legal Notices Generator",
  "goals": "Produce a Text File Legal Notices file, listing all components, licenses, and copyright information for a project.",
  "backstory": "You are an Open Source Compliance Engineer. As such, your role is to consolidate the list of packages, with license and copyright information, into a simple text file that allows display attribution to authors and copyright holders.",
  "tools": [],
  "ollama_model": "gpt-3.5-turbo"
}
```

**Features**:
- Generates compliance-ready legal notices
- Formats copyright attributions
- Ensures regulatory compliance
- Creates human-readable documentation

## Usage Examples

### Basic SBOM Analysis

```bash
# Register the workflow
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d @samples/agentic_sbom_project.json

# Execute the workflow
curl -X POST http://localhost:8000/workflows/email_test_workflow_no_agent/execute \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Custom Email Configuration

```json
{
  "email_checker": {
    "protocol": "imap",
    "server": "imap.gmail.com",
    "port": 993,
    "username": "your-email@gmail.com",
    "password": "<EMAIL_PASSWORD>",
    "folder": "INBOX",
    "unread_only": true,
    "limit": 5
  }
}
```

### SBOM Format Support

The workflow supports various SBOM formats:

1. **SPDX**: Software Package Data Exchange
2. **CycloneDX**: Lightweight SBOM standard
3. **JSON**: Custom JSON formats
4. **XML**: XML-based SBOM formats

## Expected Output

### Email Response

The workflow generates an automated email response containing:

```
Subject: Re: test SBOM - SBOM Analysis Complete

Your SBOM analysis has been completed successfully.

Please find the legal notices and license assessment attached.

Workflow Results:
[Generated legal notices content]

This analysis was performed automatically by the Agentic AI Framework.

Best regards,
SBOM Analysis System

Attachments:
- legal_notices.txt
```

### Analysis Report Structure

```json
{
  "EXECUTIVE SUMMARY": {
    "overall_risk_level": "MEDIUM",
    "total_packages_analyzed": 45,
    "key_findings": [
      "3 packages with high-risk licenses",
      "12 packages missing license information",
      "2 packages with conflicting licenses"
    ],
    "summary": "Overall assessment indicates moderate compliance risk"
  },
  "INDIVIDUAL ASSESSMENTS": {
    "pkg:npm/lodash@4.17.21": {
      "license": "MIT",
      "risk_level": "LOW",
      "copyright": "Copyright (c) 2012-2022 The Dojo Foundation",
      "legal_notices": "MIT License - Permission is hereby granted..."
    }
  },
  "PATTERN ANALYSIS": {
    "common_license_types": ["MIT", "Apache-2.0", "ISC", "BSD-3-Clause"]
  },
  "AGGREGATE STATISTICS": {
    "total_packages": 45,
    "high_risk_count": 3,
    "medium_risk_count": 8,
    "low_risk_count": 34,
    "license_distribution": {
      "MIT": 25,
      "Apache-2.0": 12,
      "ISC": 5,
      "BSD-3-Clause": 3
    }
  }
}
```

## Configuration Options

### Email Server Configuration

```json
{
  "email_config": {
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "<EMAIL_PASSWORD>",
    "use_ssl": true
  }
}
```

### SBOM Processing Options

```json
{
  "sbom_config": {
    "supported_formats": ["spdx", "cyclonedx", "json", "xml"],
    "max_file_size": "10MB",
    "extract_metadata": true,
    "validate_schema": true
  }
}
```

### License Analysis Options

```json
{
  "license_config": {
    "risk_thresholds": {
      "critical": ["GPL-3.0", "AGPL-3.0"],
      "high": ["GPL-2.0", "LGPL-2.1"],
      "medium": ["MPL-2.0", "EPL-2.0"],
      "low": ["MIT", "Apache-2.0", "BSD-3-Clause"]
    },
    "external_sources": ["clearlydefined.io", "spdx.org"],
    "cache_results": true
  }
}
```

## Best Practices

### 1. Email Security
- Use secure email connections (SSL/TLS)
- Implement proper authentication
- Monitor email access logs
- Use dedicated email accounts for automation

### 2. SBOM Processing
- Validate SBOM files before processing
- Handle large files efficiently
- Support multiple SBOM formats
- Implement error handling for malformed files

### 3. License Analysis
- Use multiple license databases
- Implement risk scoring algorithms
- Cache license information
- Provide detailed audit trails

### 4. Legal Compliance
- Ensure generated notices meet legal requirements
- Include all required copyright attributions
- Maintain compliance audit trails
- Regular review of legal templates

### 5. Error Handling
- Graceful handling of email failures
- Retry logic for network issues
- Comprehensive error logging
- User notification for failures

## Troubleshooting

### Common Issues

1. **Email Connection Problems**
   - Verify email server settings
   - Check authentication credentials
   - Ensure proper SSL/TLS configuration
   - Test with email client first

2. **SBOM Parsing Errors**
   - Validate SBOM file format
   - Check file encoding
   - Verify schema compliance
   - Handle malformed data gracefully

3. **License Analysis Failures**
   - Check external API availability
   - Verify PURL format
   - Implement fallback sources
   - Cache successful results

4. **Email Sending Issues**
   - Verify SMTP configuration
   - Check attachment size limits
   - Ensure proper email formatting
   - Test with simple messages first

### Debug Tips

1. **Enable Detailed Logging**: Monitor workflow execution logs
2. **Test Individual Steps**: Verify each step independently
3. **Check File Permissions**: Ensure proper access to email and file systems
4. **Validate Configuration**: Test all configuration parameters
5. **Monitor Resource Usage**: Check memory and CPU usage for large SBOMs

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# GitHub Actions example
- name: SBOM Analysis
  run: |
    curl -X POST http://localhost:8000/workflows/email_test_workflow_no_agent/execute \
      -H "Content-Type: application/json" \
      -d '{"sbom_file": "${{ github.workspace }}/sbom.json"}'
```

### Automated Compliance Checking

```bash
#!/bin/bash
# Daily compliance check script
curl -X POST http://localhost:8000/workflows/email_test_workflow_no_agent/execute \
  -H "Content-Type: application/json" \
  -d '{"schedule": "daily", "notification": "compliance-team@company.com"}'
```

The SBOM Email Workflow provides a comprehensive solution for automated software compliance analysis, enabling organizations to maintain proper license compliance while reducing manual effort and ensuring consistent reporting. 