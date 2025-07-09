import feedparser
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional, Any
from .base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class RSSFeedParserTool(BaseTool):
    """
    RSS Feed Parser Tool for extracting structured data from RSS/Atom feeds.
    Supports Hacker News feeds and general RSS/Atom formats.
    """
    
    @property
    def name(self) -> str:
        return "rss_feed_parser"
    
    @property
    def description(self) -> str:
        return "Parse RSS/Atom feeds and extract structured article data"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "feed_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of RSS feed URLs to parse"
                },
                "max_items": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of items to extract per feed"
                },
                "include_content": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to fetch full content"
                },
                "rate_limit": {
                    "type": "number",
                    "default": 1,
                    "description": "Delay between requests in seconds"
                }
            },
            "required": ["feed_urls"]
        }
        
    async def execute(self, parameters: Dict[str, Any]) -> Any:
        """
        Parse RSS/Atom feeds and extract structured data.
        
        Args:
            input_data: Dictionary containing:
                - feed_urls: List of RSS feed URLs to parse
                - max_items: Maximum number of items to extract per feed (default: 10)
                - include_content: Whether to fetch full content (default: False)
                - rate_limit: Delay between requests in seconds (default: 1)
        
        Returns:
            Dictionary containing parsed feed data
        """
        try:
            feed_urls = parameters.get("feed_urls", [])
            max_items = parameters.get("max_items", 10)
            include_content = parameters.get("include_content", False)
            rate_limit = parameters.get("rate_limit", 1)
            
            if not feed_urls:
                return {
                    "success": False,
                    "error": "No feed URLs provided",
                    "results": []
                }
            
            all_results = []
            total_feeds = len(feed_urls)
            successful_feeds = 0
            failed_feeds = 0
            
            for feed_url in feed_urls:
                try:
                    logger.info(f"Parsing feed: {feed_url}")
                    
                    # Parse the RSS feed
                    feed_result = self._parse_feed(
                        feed_url, 
                        max_items, 
                        include_content
                    )
                    
                    if feed_result["success"]:
                        all_results.append(feed_result)
                        successful_feeds += 1
                    else:
                        failed_feeds += 1
                        logger.warning(f"Failed to parse feed {feed_url}: {feed_result.get('error')}")
                    
                    # Rate limiting
                    if rate_limit > 0:
                        import time
                        time.sleep(rate_limit)
                        
                except Exception as e:
                    failed_feeds += 1
                    logger.error(f"Error parsing feed {feed_url}: {str(e)}")
                    all_results.append({
                        "feed_url": feed_url,
                        "success": False,
                        "error": str(e),
                        "items": []
                    })
            
            return {
                "success": successful_feeds > 0,
                "total_feeds": total_feeds,
                "successful_feeds": successful_feeds,
                "failed_feeds": failed_feeds,
                "results": all_results,
                "message": f"Parsed {successful_feeds}/{total_feeds} feeds successfully"
            }
            
        except Exception as e:
            logger.error(f"RSS feed parser error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def _parse_feed(self, feed_url: str, max_items: int, include_content: bool) -> Dict[str, Any]:
        """
        Parse a single RSS/Atom feed.
        
        Args:
            feed_url: URL of the RSS feed
            max_items: Maximum number of items to extract
            include_content: Whether to fetch full content
            
        Returns:
            Dictionary containing parsed feed data
        """
        try:
            # Fetch and parse the feed
            response = requests.get(feed_url, timeout=30)
            response.raise_for_status()
            
            # Parse with feedparser
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"Feed parsing warnings for {feed_url}: {feed.bozo_exception}")
            
            # Extract feed metadata
            feed_info = {
                "title": feed.feed.get("title", ""),
                "description": feed.feed.get("description", ""),
                "link": feed.feed.get("link", ""),
                "language": feed.feed.get("language", ""),
                "updated": feed.feed.get("updated", ""),
                "generator": feed.feed.get("generator", "")
            }
            
            # Extract items
            items = []
            for i, entry in enumerate(feed.entries[:max_items]):
                try:
                    item = self._extract_item_data(entry, include_content)
                    items.append(item)
                except Exception as e:
                    logger.warning(f"Error extracting item {i} from {feed_url}: {str(e)}")
                    continue
            
            return {
                "feed_url": feed_url,
                "success": True,
                "feed_info": feed_info,
                "items": items,
                "total_items": len(items),
                "parsed_at": datetime.utcnow().isoformat()
            }
            
        except requests.RequestException as e:
            return {
                "feed_url": feed_url,
                "success": False,
                "error": f"Network error: {str(e)}",
                "items": []
            }
        except Exception as e:
            return {
                "feed_url": feed_url,
                "success": False,
                "error": f"Parsing error: {str(e)}",
                "items": []
            }
    
    def _extract_item_data(self, entry, include_content: bool) -> Dict[str, Any]:
        """
        Extract structured data from a feed item.
        
        Args:
            entry: Feedparser entry object
            include_content: Whether to include full content
            
        Returns:
            Dictionary containing item data
        """
        # Basic item data
        item = {
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "description": entry.get("description", ""),
            "published": entry.get("published", ""),
            "updated": entry.get("updated", ""),
            "author": entry.get("author", ""),
            "id": entry.get("id", ""),
            "tags": [tag.term for tag in entry.get("tags", [])],
            "category": entry.get("category", ""),
            "comments": entry.get("comments", ""),
            "comment_count": entry.get("comment_count", 0),
            "points": entry.get("points", 0),
            "comments_url": entry.get("comments_url", "")
        }
        
        # Hacker News specific data
        if "hnrss.org" in entry.get("link", ""):
            item.update(self._extract_hn_data(entry))
        
        # Include full content if requested
        if include_content:
            content = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else ""
            if not content:
                content = entry.get("summary", "")
            item["full_content"] = content
        
        return item
    
    def _extract_hn_data(self, entry) -> Dict[str, Any]:
        """
        Extract Hacker News specific data from feed entry.
        
        Args:
            entry: Feedparser entry object
            
        Returns:
            Dictionary containing HN-specific data
        """
        hn_data = {}
        
        # Extract points from description if available
        description = entry.get("description", "")
        if "Points:" in description:
            try:
                points_text = description.split("Points:")[1].split()[0]
                hn_data["points"] = int(points_text)
            except (ValueError, IndexError):
                hn_data["points"] = 0
        
        # Extract comment count from description
        if "# Comments:" in description:
            try:
                comments_text = description.split("# Comments:")[1].split()[0]
                hn_data["comment_count"] = int(comments_text)
            except (ValueError, IndexError):
                hn_data["comment_count"] = 0
        
        # Extract comments URL
        if "Comments URL:" in description:
            try:
                comments_url = description.split("Comments URL:")[1].split()[0]
                hn_data["comments_url"] = comments_url
            except IndexError:
                hn_data["comments_url"] = ""
        
        # Extract article URL
        if "Article URL:" in description:
            try:
                article_url = description.split("Article URL:")[1].split()[0]
                hn_data["article_url"] = article_url
            except IndexError:
                hn_data["article_url"] = ""
        
        return hn_data 