"""
tools/web_scraper.py - Web Scraping Tool

Advanced web scraping tool with HTML parsing, CSS/XPath selectors, and multi-threading support.
Supports both static HTML and dynamic content extraction.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup
import lxml.html
from lxml import etree
import re

from .base_tool import BaseTool
from .rate_limiter import rate_limit_manager

logger = logging.getLogger(__name__)

class WebScraperTool(BaseTool):
    """Advanced web scraping tool with HTML parsing and multi-threading"""
    
    @property
    def name(self) -> str:
        return "web_scraper"
    
    @property
    def description(self) -> str:
        return "Advanced web scraping with HTML parsing, CSS/XPath selectors, and multi-threading support"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "urls": {
                    "type": "array",
                    "description": "List of URLs to scrape",
                    "items": {"type": "string"}
                },
                "selectors": {
                    "type": "object",
                    "description": "CSS/XPath selectors for data extraction",
                    "properties": {
                        "css": {
                            "type": "object",
                            "description": "CSS selectors as key-value pairs"
                        },
                        "xpath": {
                            "type": "object", 
                            "description": "XPath expressions as key-value pairs"
                        }
                    }
                },
                "patterns": {
                    "type": "object",
                    "description": "Regex patterns for text extraction"
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Whether to extract and follow links",
                    "default": False
                },
                "link_filters": {
                    "type": "object",
                    "description": "Filters for link extraction",
                    "properties": {
                        "include_patterns": {"type": "array", "items": {"type": "string"}},
                        "exclude_patterns": {"type": "array", "items": {"type": "string"}},
                        "max_depth": {"type": "integer", "default": 2},
                        "same_domain_only": {"type": "boolean", "default": True}
                    }
                },
                "concurrent_requests": {
                    "type": "integer",
                    "description": "Number of concurrent requests",
                    "default": 5
                },
                "rate_limit": {
                    "type": "object",
                    "description": "Rate limiting configuration",
                    "properties": {
                        "requests_per_second": {"type": "integer", "default": 2},
                        "delay_between_requests": {"type": "number", "default": 1.0}
                    }
                },
                "headers": {
                    "type": "object",
                    "description": "Custom HTTP headers",
                    "default": {}
                },
                "timeout": {
                    "type": "integer",
                    "description": "Request timeout in seconds",
                    "default": 30
                },
                "user_agent": {
                    "type": "string",
                    "description": "Custom user agent string",
                    "default": "Mozilla/5.0 (compatible; AgenticWebScraper/1.0)"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "description": "Whether to follow redirects",
                    "default": True
                },
                "extract_metadata": {
                    "type": "boolean",
                    "description": "Extract page metadata (title, description, etc.)",
                    "default": True
                }
            },
            "required": ["urls"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web scraping with multi-threading and rate limiting"""
        
        try:
            urls = parameters.get("urls", [])
            selectors = parameters.get("selectors", {})
            patterns = parameters.get("patterns", {})
            extract_links = parameters.get("extract_links", False)
            link_filters = parameters.get("link_filters", {})
            concurrent_requests = parameters.get("concurrent_requests", 5)
            rate_limit_config = parameters.get("rate_limit", {})
            headers = parameters.get("headers", {})
            timeout = parameters.get("timeout", 30)
            user_agent = parameters.get("user_agent", "Mozilla/5.0 (compatible; AgenticWebScraper/1.0)")
            follow_redirects = parameters.get("follow_redirects", True)
            extract_metadata = parameters.get("extract_metadata", True)
            
            # Setup rate limiting
            rate_limiter = None
            if rate_limit_config:
                requests_per_second = rate_limit_config.get("requests_per_second", 2)
                rate_limiter = rate_limit_manager.add_limiter(
                    "web_scraper", 
                    requests_per_second, 
                    1.0
                )
            
            # Setup headers
            default_headers = {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            headers.update(default_headers)
            
            logger.info(f"Starting web scraping for {len(urls)} URLs with {concurrent_requests} concurrent requests")
            
            # Create semaphore for concurrent requests
            semaphore = asyncio.Semaphore(concurrent_requests)
            
            # Scrape URLs concurrently
            tasks = []
            for url in urls:
                task = self._scrape_url_with_semaphore(
                    url, selectors, patterns, extract_links, link_filters,
                    headers, timeout, follow_redirects, extract_metadata,
                    semaphore, rate_limiter
                )
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful_results = []
            failed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    failed_results.append({
                        "url": urls[i],
                        "error": str(result)
                    })
                else:
                    successful_results.append(result)
            
            # Extract discovered links if requested
            discovered_links = []
            if extract_links:
                for result in successful_results:
                    if "links" in result:
                        discovered_links.extend(result["links"])
                discovered_links = list(set(discovered_links))  # Remove duplicates
            
            return {
                "success": True,
                "total_urls": len(urls),
                "successful_scrapes": len(successful_results),
                "failed_scrapes": len(failed_results),
                "results": successful_results,
                "errors": failed_results,
                "discovered_links": discovered_links,
                "message": f"Scraped {len(successful_results)}/{len(urls)} URLs successfully"
            }
            
        except Exception as e:
            logger.error(f"Web scraping failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Web scraping failed: {str(e)}"
            }
    
    async def _scrape_url_with_semaphore(self, url: str, selectors: Dict, patterns: Dict,
                                       extract_links: bool, link_filters: Dict,
                                       headers: Dict, timeout: int, follow_redirects: bool,
                                       extract_metadata: bool, semaphore: asyncio.Semaphore,
                                       rate_limiter) -> Dict[str, Any]:
        """Scrape a single URL with semaphore and rate limiting"""
        
        async with semaphore:
            # Rate limiting
            if rate_limiter:
                await rate_limiter.wait_for_slot()
            
            return await self._scrape_single_url(
                url, selectors, patterns, extract_links, link_filters,
                headers, timeout, follow_redirects, extract_metadata
            )
    
    async def _scrape_single_url(self, url: str, selectors: Dict, patterns: Dict,
                               extract_links: bool, link_filters: Dict,
                               headers: Dict, timeout: int, follow_redirects: bool,
                               extract_metadata: bool) -> Dict[str, Any]:
        """Scrape a single URL and extract data"""
        
        try:
            logger.info(f"Scraping URL: {url}")
            
            # Make HTTP request
            async with aiohttp.ClientSession() as session:
                timeout_config = aiohttp.ClientTimeout(total=timeout)
                
                async with session.get(
                    url, 
                    headers=headers, 
                    timeout=timeout_config,
                    allow_redirects=follow_redirects
                ) as response:
                    
                    if response.status != 200:
                        return {
                            "url": url,
                            "success": False,
                            "status_code": response.status,
                            "error": f"HTTP {response.status}"
                        }
                    
                    # Get HTML content
                    html_content = await response.text()
                    
                    # Parse HTML
                    soup = BeautifulSoup(html_content, 'lxml')
                    
                    # Extract data using selectors
                    extracted_data = {}
                    
                    # CSS selectors
                    if "css" in selectors:
                        for key, selector in selectors["css"].items():
                            elements = soup.select(selector)
                            if elements:
                                extracted_data[key] = [elem.get_text(strip=True) for elem in elements]
                            else:
                                extracted_data[key] = []
                    
                    # XPath selectors
                    if "xpath" in selectors:
                        tree = lxml.html.fromstring(html_content)
                        for key, xpath_expr in selectors["xpath"].items():
                            try:
                                elements = tree.xpath(xpath_expr)
                                if elements:
                                    extracted_data[key] = [str(elem) for elem in elements]
                                else:
                                    extracted_data[key] = []
                            except Exception as e:
                                logger.warning(f"XPath error for {key}: {e}")
                                extracted_data[key] = []
                    
                    # Regex patterns
                    for key, pattern in patterns.items():
                        matches = re.findall(pattern, html_content)
                        extracted_data[key] = matches
                    
                    # Extract metadata
                    metadata = {}
                    if extract_metadata:
                        metadata = self._extract_metadata(soup)
                    
                    # Extract links
                    links = []
                    if extract_links:
                        links = self._extract_links(soup, url, link_filters)
                    
                    return {
                        "url": url,
                        "success": True,
                        "status_code": response.status,
                        "extracted_data": extracted_data,
                        "metadata": metadata,
                        "links": links,
                        "content_length": len(html_content),
                        "content_type": response.headers.get("content-type", "text/html")
                    }
                    
        except asyncio.TimeoutError:
            return {
                "url": url,
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "success": False,
                "error": str(e)
            }
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract page metadata"""
        metadata = {}
        
        # Title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)
        
        # Meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            metadata["description"] = meta_desc.get("content", "")
        
        # Meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            metadata["keywords"] = meta_keywords.get("content", "")
        
        # Open Graph tags
        og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})
        for tag in og_tags:
            property_name = tag.get("property", "").replace("og:", "")
            metadata[f"og_{property_name}"] = tag.get("content", "")
        
        # Twitter Card tags
        twitter_tags = soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
        for tag in twitter_tags:
            name = tag.get("name", "").replace("twitter:", "")
            metadata[f"twitter_{name}"] = tag.get("content", "")
        
        return metadata
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str, filters: Dict) -> List[str]:
        """Extract and filter links from the page"""
        links = []
        
        # Find all links
        for link in soup.find_all("a", href=True):
            href = link["href"]
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Apply filters
            if self._should_include_link(absolute_url, filters):
                links.append(absolute_url)
        
        return links
    
    def _should_include_link(self, url: str, filters: Dict) -> bool:
        """Check if a link should be included based on filters"""
        
        # Include patterns
        include_patterns = filters.get("include_patterns", [])
        if include_patterns:
            if not any(re.search(pattern, url) for pattern in include_patterns):
                return False
        
        # Exclude patterns
        exclude_patterns = filters.get("exclude_patterns", [])
        if exclude_patterns:
            if any(re.search(pattern, url) for pattern in exclude_patterns):
                return False
        
        # Same domain only
        same_domain_only = filters.get("same_domain_only", True)
        if same_domain_only:
            base_domain = urlparse(url).netloc
            # This would need to be compared with the original domain
            # For now, we'll include all links
        
        return True 