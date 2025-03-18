import os
import random
import time
import re
import feedparser
from datetime import datetime

from dotenv import load_dotenv

from models import get_model
from state import State, NewsArticle

# Load environment variables
load_dotenv()

# Determine model name and initialize the LLM
model_name = os.getenv("MODEL", "local")
base_llm = get_model("ollama/gemma2") if model_name == "local" else get_model("openai/gpt-4o-mini")

def get_timestamp() -> str:
    """Get current timestamp in HH:MM:SS format."""
    return datetime.now().strftime("%H:%M:%S")

def print_with_timestamp(message: str) -> None:
    """Print a message with current timestamp."""
    print(f"[{get_timestamp()}] {message}")

def print_step(step_name: str, status: str = "started") -> None:
    """Print the current step with timestamp and status."""
    emoji = {
        "started": "🚀",
        "completed": "✅",
        "failed": "❌",
        "skipped": "⏭️",
        "rewriting": "✍️"
    }.get(status, "📝")
    print_with_timestamp(f"{emoji} {step_name} - {status}")

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
    print_step("Fetching AI News from RSS Feed")
    try:
        feed = feedparser.parse("https://buttondown.com/ainews/rss", sanitize_html=True)
        if not feed.entries:
            print_step("Fetching AI News from RSS Feed", "failed - no entries found")
            return State(error="No entries found in the RSS feed.")

        # Get today's news from the first feed entry (each entry represents one day)
        result = feed.entries[0].summary
        headlines = re.findall(r"(?s)<h3.*?>(?P<headline>.*?)</h3>(.*?)<hr />", result)

        articles = []
        for headline, content in headlines:
            headline_text = re.sub(r"<[^>]+>", "", headline).strip()
            content_text = re.sub(r"<[^>]+>", "", content).strip()
            links = re.findall(r'https?://\S+', content)
            url = links[0] if links else ""

            articles.append(NewsArticle(title=headline_text, content=content_text, url=url))

        print_step("Fetching AI News from RSS Feed", f"completed - found {len(articles)} articles")
        return State(news_articles=articles)
    
    except Exception as e:
        print_step("Fetching AI News from RSS Feed", f"failed - {str(e)}")
        return State(error=str(e))


def choose_relevant_article_node(state: State) -> State:
    """
    Choose the 5 most relevant AI articles from the search results.
    
    Selection criteria:
    1. Scientific breakthroughs in AI
    2. Technical innovations in specific domains
    3. Recent publication (within last 4 weeks)
    
    Args:
        state: Current workflow state with search results
        
    Returns:
        Updated state with selected articles (up to 5)
    """
    print_step("Choosing Most Relevant Articles")
    state.current_node = "choose_relevant_article"
    if not state.news_articles:
        print_step("Choosing Most Relevant Articles", "failed - no articles available")
        state.error = "No articles available to choose from"
        return state

    # Filter out duplicate articles based on title and content
    unique_articles = []
    seen_titles = set()
    seen_contents = set()
    
    for article in state.news_articles:
        # Create a normalized version of the title and content for comparison
        norm_title = article.title.lower().strip()
        norm_content = article.content[:200].lower().strip()  # Compare first 200 chars to avoid duplicates with slight variations
        
        if norm_title not in seen_titles and norm_content not in seen_contents:
            unique_articles.append(article)
            seen_titles.add(norm_title)
            seen_contents.add(norm_content)

    if not unique_articles:
        print_step("Choosing Most Relevant Articles", "failed - no unique articles found")
        state.error = "No unique articles available to choose from"
        return state

    prompt = """
        Select the 5 most relevant articles from the provided list of news articles.
        Respond with a comma-separated list of article numbers (0-based index, so 0 for the first article, 1 for the second, etc.).
        Only the numbers separated by commas, so I can parse them without errors.
        Relevance should be based on:

        1. Scientific breakthroughs in Artificial Intelligence (new publications, new approaches, new models, new open-source libraries).
        2. Technical innovations and disruptions in Artificial Intelligence for the domains: manufacturing, computer vision, robotics, and aerospace.
        3. The article should be recent (published within the last 4 weeks).

        Here are the articles to choose from:
        {articles}
    """

    # Format articles for the prompt
    articles_text = "\n\n".join(
        f"{i}. {article.title}\n{article.content}\n\n"
        for i, article in enumerate(unique_articles)
    )
    
    try:
        msg = base_llm.invoke(prompt.format(articles=articles_text))
        selected_indices = [int(idx.strip()) for idx in msg.content.split(",")]
        
        # Validate indices and limit to 5
        valid_indices = [idx for idx in selected_indices if 0 <= idx < len(unique_articles)][:5]
            
        if not valid_indices:
            print_step("Choosing Most Relevant Articles", "failed - no valid indices found")
            state.error = "No valid article indices were selected"
            return state
            
        state.selected_articles = [unique_articles[idx] for idx in valid_indices]
        print_step("Choosing Most Relevant Articles", f"completed - selected {len(state.selected_articles)} unique articles")
    except ValueError as e:
        print_step("Choosing Most Relevant Articles", f"failed - invalid response: {msg.content}")
        state.error = f"Error in 'choose_relevant_article': Could not parse LLM response as integers. Response was: {msg.content}"
    except Exception as e:
        print_step("Choosing Most Relevant Articles", f"failed - {str(e)}")
        state.error = f"Unexpected error in 'choose_relevant_article': {str(e)}"
    
    return state

def select_article_node(state: State) -> State:
    """
    Let the user select which article to use for the LinkedIn post.
    
    Args:
        state: Current workflow state containing the selected articles
        
    Returns:
        Updated state with the user-selected article
    """
    print_step("Selecting Article for LinkedIn Post")
    state.current_node = "select_article"
    
    if not state.selected_articles:
        print_step("Selecting Article", "failed - no articles available")
        state.error = "No articles available for selection"
        return state
    
    # Display articles to the user
    print("\n")
    print_with_timestamp("📰 Available Articles:")
    print_with_timestamp("-" * 80)
    for i, article in enumerate(state.selected_articles, 1):
        print("\n")
        print_with_timestamp(f"{i}. {article.title}")
        print_with_timestamp(f"   {article.content[:200]}...")
        print_with_timestamp(f"   URL: {article.url}")
        print_with_timestamp("-" * 80)
    
    # Get user selection
    while True:
        try:
            choice = int(input(f"\n[{get_timestamp()}] Enter the number of the article you want to use (1-5): ").strip())
            if 1 <= choice <= len(state.selected_articles):
                state.linkedin_article = state.selected_articles[choice - 1]
                print_step("Selecting Article", f"completed - selected article {choice}")
                break
            else:
                print_with_timestamp(f"Please enter a number between 1 and {len(state.selected_articles)}")
        except ValueError:
            print_with_timestamp("Please enter a valid number")
    
    return state


def generate_linkedin_post_node(state: State) -> State:
    """
    Generate a LinkedIn post from the chosen article.
    """
    print_step("Generating LinkedIn Post")
    
    # Base prompt for post generation
    base_prompt = """
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
    """

    # If we have previous feedback, incorporate it
    if state.quality_evaluation and state.needs_rewrite:
        print_step("Generating LinkedIn Post", "rewriting based on user feedback")
        prompt = f"""
            {base_prompt}

            The previous version of the post needs improvement based on user feedback.
            Here's the context:

            Original Post:
            {state.linkedin_post}

            User Feedback:
            {state.quality_evaluation['feedback']}
            
            Article to write about:
            {{article}}

            Please generate an improved version of the post that addresses the user's feedback while maintaining the same high-quality structure and style.
        """
    else:
        prompt = f"{base_prompt}\n\nArticle to write about:\n{{article}}"

    try:
        msg = base_llm.invoke(prompt.format(article=state.linkedin_article.content))
        state.linkedin_post = msg.content
        print_step("Generating LinkedIn Post", "completed")
    except Exception as e:
        print_step("Generating LinkedIn Post", f"failed - {str(e)}")
        state.error = f"Error generating LinkedIn post: {str(e)}"
    
    return state


def get_user_feedback_node(state: State) -> State:
    """
    Get user feedback on the generated LinkedIn post.
    This is a human-in-the-loop node that allows users to provide feedback
    and decide whether to save or improve the post.
    
    Args:
        state: Current workflow state containing the LinkedIn post
        
    Returns:
        Updated state with user feedback and rewrite decision
    """
    print_step("Getting User Feedback")
    state.current_node = "get_user_feedback"
    
    if not state.linkedin_post:
        print_step("Getting User Feedback", "failed - no post available")
        state.error = "No LinkedIn post available for feedback"
        return state
    
    # Show the generated post to the user
    print("\n")
    print("-" * 80)
    print(state.linkedin_post)
    print("-" * 80)
    
    # Ask for user feedback
    print_with_timestamp("\nWould you like to:")
    print_with_timestamp("1. Save this version")
    print_with_timestamp("2. Provide feedback for improvement")
    
    while True:
        choice = input(f"\n[{get_timestamp()}] Enter your choice (1 or 2): ").strip()
        if choice == "1":
            state.needs_rewrite = False
            print_step("Getting User Feedback", "completed - post approved")
            break
        elif choice == "2":
            feedback = input(f"\n[{get_timestamp()}] Please provide your feedback for improvement: ").strip()
            if feedback:
                state.quality_evaluation = {"feedback": feedback}
                state.needs_rewrite = True
                print_step("Getting User Feedback", "completed - feedback received")
                break
            else:
                print_with_timestamp("Feedback cannot be empty. Please try again.")
        else:
            print_with_timestamp("Please enter 1 or 2")
    
    return state


def gather_additional_info_node(state: State) -> State:
    """
    Gather additional information using Tavily search when needed.
    
    Args:
        state: Current workflow state containing quality evaluation results
        
    Returns:
        Updated state with additional information
    """
    print_step("Gathering Additional Information")
    state.current_node = "gather_additional_info"
    
    if not state.needs_rewrite:
        print_step("Gathering Additional Information", "skipped - not needed")
        return state
        
    try:
        from tools import gather_additional_info
        
        # Create a search query based on the article title and content
        search_query = f"{state.linkedin_article.title} {state.linkedin_article.content[:200]}"
        state.additional_info = gather_additional_info(search_query)
        print_step("Gathering Additional Information", "completed")
    except Exception as e:
        print_step("Gathering Additional Information", f"failed - {str(e)}")
        state.error = f"Error gathering additional information: {str(e)}"
    
    return state



def save_linkedin_post_node(state: State) -> State:
    """
    Save the generated LinkedIn post to a file.
    
    Args:
        state: Current workflow state containing the LinkedIn post
        
    Returns:
        Updated state with file save status
    """
    print_step("Saving LinkedIn Post")
    state.current_node = "save_linkedin_post"
    
    try:
        with open("linkedin_post.txt", "w", encoding="utf-8") as f:
            f.write(state.linkedin_post)
        print_step("Saving LinkedIn Post", "completed")
    except Exception as e:
        print_step("Saving LinkedIn Post", f"failed - {str(e)}")
        state.error = f"Failed to save LinkedIn post to file: {str(e)}"
    
    return state
