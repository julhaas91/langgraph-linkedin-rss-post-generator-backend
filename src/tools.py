from typing import List, Dict
import feedparser
from datetime import datetime

from langchain_community.tools import TavilySearchResults
from state import NewsArticle

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


def gather_additional_info(query: str, max_results: int = 3) -> str:
    """
    Gather additional information using Tavily search.
    
    Args:
        query: The search query
        max_results: Maximum number of search results to return
        
    Returns:
        Combined information from search results
    """
    tool = tavily_search_tool(max_results=max_results)
    try:
        results = tool({"query": query})
        
        # Combine information from search results
        combined_info = []
        for result in results:
            if result.get("content"):
                combined_info.append(result["content"])
            if result.get("answer"):
                combined_info.append(result["answer"])
                
        return "\n\n".join(combined_info)
    except Exception as e:
        return f"Error gathering additional information: {str(e)}"


def tavily_search_tool(max_results: int = 5, search_depth: str = "advanced", include_answer: bool = True, include_raw_content: bool = True, include_images: bool = True) -> TavilySearchResults:
    """Tool to search the web for additional information about a topic."""
    return TavilySearchResults(
        max_results=max_results,
        search_depth=search_depth,
        include_answer=include_answer,
        include_raw_content=include_raw_content,
        include_images=include_images,
        name="tavily_search_tool"
    )