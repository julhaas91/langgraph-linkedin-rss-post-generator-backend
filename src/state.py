from pydantic import BaseModel, Field
from typing import List, Optional
from langgraph.graph import START

class NewsArticle(BaseModel):
    title: str = Field(default="", description="Title of the news article")
    content: str = Field(default="", description="Content of the news article")
    type: str = Field(default="general", description="Type of the news article (e.g. general, scientific publication, X / Twitter feed)")
    url: str = Field(default="", description="URL of the news article")


# Graph State
class State(BaseModel):
    search_results: Optional[List[dict]] = Field(default=None, description="List of search results")
    news_articles: Optional[List[NewsArticle]] = Field(default=None, description="List of news articles")
    linkedin_article: Optional[NewsArticle] = Field(default=None, description="Article for LinkedIn post generation")
    linkedin_post: Optional[str] = Field(default=None, description="LinkedIn post generated from the article")
    current_node: Optional[str] = Field(default=START, description="Current node in the workflow")
    error: Optional[str] = Field(default=None, description="Error message if any")
    