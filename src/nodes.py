import os
import random
import time
import re
import feedparser

from dotenv import load_dotenv

from models import get_model
from state import State, NewsArticle
# from tools import tavily_search_tool

# Load environment variables
load_dotenv()

# Determine model name and initialize the LLM
model_name = os.getenv("MODEL", "local")
llm = get_model("ollama/gemma2") if model_name == "local" else get_model("openai/gpt-4o-mini")



def fetch_ai_news_rss_node(state: State) -> State:
    """
    Fetches and parses the latest AI news from a specific RSS feed.

    This function retrieves the most recent entry from the AI News RSS feed,
    extracts headlines, their corresponding content, and any links within the content.
    It stores them as a list of NewsArticle objects and returns the updated State.

    Args:
        state: Current workflow state

    Returns:
        State: Updated state containing all the fetched news articles.
    """
    try:
        feed = feedparser.parse("https://buttondown.com/ainews/rss", sanitize_html=True)
        if not feed.entries:
            return State(error="No entries found in the RSS feed.")

        result = feed.entries[0].summary
        headlines = re.findall(r"(?s)<h3.*?>(?P<headline>.*?)</h3>(.*?)<hr />", result)

        articles = []
        for headline, content in headlines:
            headline_text = re.sub(r"<[^>]+>", "", headline).strip()
            content_text = re.sub(r"<[^>]+>", "", content).strip()
            links = re.findall(r'https?://\S+', content)
            url = links[0] if links else ""

            articles.append(NewsArticle(title=headline_text, content=content_text, url=url))

        return State(news_articles=articles)
    
    except Exception as e:
        return State(error=str(e))



# def search_web_node(state: State, max_results: int = 5, max_retries: int = 5) -> State:
#     """
#     Search the web for the latest news on AI.
    
#     Args:
#         state: Current workflow state
#         max_results: Maximum number of search results to return
#         max_retries: Maximum number of retry attempts on failure
        
#     Returns:
#         Updated state with search results or error information
#     """
#     state.current_node = "search_web"
#     query = "Latest Artificial Intelligence News"
#     tool = tavily_search_tool(max_results=max_results)
    
#     attempt = 0
#     while attempt < max_retries:
#         try:
#             state.search_results = tool({"query": query})
#             return state
#         except Exception as e:
#             attempt += 1
#             wait_time = 2 ** attempt + random.uniform(0, 1)  # Exponential backoff with jitter
#             error_msg = f"Error: {e}. Retrying in {wait_time:.2f} seconds... ({attempt}/{max_retries})"
#             print(error_msg)
#             state.error += error_msg
#             time.sleep(wait_time)
            
#     state.error += "Search failed due to repeated errors. Try again later."
#     return state


def choose_relevant_article_node(state: State) -> State:
    """
    Choose the most relevant AI article from the search results.
    
    Selection criteria:
    1. Scientific breakthroughs in AI
    2. Technical innovations in specific domains
    3. Recent publication (within last 4 weeks)
    
    Args:
        state: Current workflow state with search results
        
    Returns:
        Updated state with selected article
    """
    state.current_node = "choose_relevant_article"
    if not state.news_articles:
        state.error = "No articles available to choose from"
        return state

    prompt = """
        Select the most relevant article from the provided list of news articles.
        Respond only with the article number (0-based index, so 0 for the first article, 1 for the second, etc.).
        Only the number, so I can cast it to int without errors.
        Relevance should be based on:

        1. Scientific breakthroughs in Artificial Intelligence (new publications, new approaches, new models, new open-source libraries).
        2. Technical innovations and disruptions in Artificial Intelligence for the domains: manufacturing, computer vision, robotics, and aerospace.
        3. The article should be recent (published within the last 4 weeks).

        Here are the articles to choose from:
        {articles}
    """

    # Format articles for the prompt
    articles_text = "\n\n".join(
        f"{i}. {article.title}\n{article.content}"
        for i, article in enumerate(state.news_articles)
    )
    
    try:
        msg = llm.invoke(prompt.format(articles=articles_text))
        selected_index = int(msg.content.strip())
        
        if selected_index < 0 or selected_index >= len(state.news_articles):
            state.error = f"Selected index {selected_index} is out of bounds. Must be between 0 and {len(state.news_articles) - 1}"
            return state
            
        state.linkedin_article = state.news_articles[selected_index]
    except ValueError as e:
        state.error = f"Error in 'choose_relevant_article': Could not parse LLM response as integer. Response was: {msg.content}"
    except Exception as e:
        state.error = f"Unexpected error in 'choose_relevant_article': {str(e)}"
    
    return state


def generate_linkedin_post_node(state: State) -> State:
    """
    Generate a LinkedIn post from the chosen article.
    
    Args:
        state: Current workflow state with selected article
        
    Returns:
        Updated state with generated LinkedIn post
    """
    state.current_node = "generate_linkedin_post"

    prompt = """
        Create an engaging LinkedIn post about this article. Follow these guidelines:

        STRUCTURE:
        1. Hook (1 line): Start with a compelling insight or observation
        2. Context (2-3 lines): Connect the topic to real-world impact
        3. Key Insights (2-4 lines): Share main takeaways in clear, concise points
        4. Value (1 line): Highlight professional significance
        5. Call to Action: End with an engaging question or prompt

        WRITING STYLE:
        - Use clear, straightforward language
        - Write short, impactful sentences
        - Organize ideas with bullet points
        - Add frequent line breaks between concepts
        - Use active voice
        - Focus on practical, actionable insights
        - Support points with specific examples or data
        - Address the reader directly using "you" and "your"
        - Pose thought-provoking questions
        - Skip introductory phrases like "in conclusion" or "in summary"
        - Avoid warnings, notes, or unnecessary extras

        AVOID:
        - Emojis, hashtags, semicolons, and asterisks
        - Clichés and metaphors
        - Broad generalizations
        - Passive voice
        - These words: Accordingly, Additionally, Arguably, Certainly, Consequently, Hence, However, Indeed, Moreover, Nevertheless, Nonetheless, Notwithstanding, Thus, Undoubtedly, Adept, Commendable, Dynamic

        Article to write about:
        {article}
    """

    msg = llm.invoke(prompt.format(article=state.linkedin_article))
    state.linkedin_post = msg.content
    return state


def save_linkedin_post_node(state: State) -> State:
    """
    Save the generated LinkedIn post to a file.
    
    Args:
        state: Current workflow state containing the LinkedIn post
        
    Returns:
        Updated state with file save status
    """
    state.current_node = "save_linkedin_post"
    
    try:
        with open("linkedin_post.txt", "w", encoding="utf-8") as f:
            f.write(state.linkedin_post)
    except Exception as e:
        state.error = f"Failed to save LinkedIn post to file: {str(e)}"
    
    return state
