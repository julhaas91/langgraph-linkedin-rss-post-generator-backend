from typing import List, Dict
import feedparser
from datetime import datetime

from langchain_community.tools import TavilySearchResults
from state import NewsArticle

# def tavily_search_tool(max_results: int = 5, search_depth: str = "advanced", include_answer: bool = True, include_raw_content: bool = True, include_images: bool = True) -> TavilySearchResults:
#     """Tool to search the web for the latest news on a given topic."""
#     return TavilySearchResults(
#         max_results=5,
#         search_depth="advanced",
#         include_answer=True,
#         include_raw_content=True,
#         include_images=True,
#         name="tavily_search_tool"
#         # include_domains=[...],
#         # exclude_domains=[...],
#         # description="",                 # overwrite default tool description
#         # args_schema=...,             # overwrite default args_schema: BaseModel
#     )


def fetch_rss_feed(url: str, limit: int = 50) -> List[Dict[str, str]]:
    """
    Fetches news articles from an RSS feed.
    
    Args:
        url: URL of the RSS feed
        limit: Maximum number of articles to return
        
    Returns:
        List of news articles
    """
    try:
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:limit]:
            article = NewsArticle(
                title=entry.title,
                url=entry.link,
                summary=entry.get('summary', ''),
                published_date=entry.get('published', datetime.now().isoformat()),
                source=feed.feed.title
            )
            articles.append(article.model_dump())
            
        return articles
    except Exception as e:
        return [{"error": f"Failed to fetch RSS feed: {str(e)}"}]
