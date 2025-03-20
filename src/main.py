"""
AI News Workflow that fetches, filters, and creates LinkedIn posts.

This module creates a workflow that:
1. Searches the web for the latest AI news
2. Selects a relevant article based on predefined criteria
3. Generates a LinkedIn post about the selected article
4. Evaluates the quality of the post and improves it if needed

Based on https://langchain-ai.github.io/langgraph/tutorials/workflows/
"""

import os
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from models import get_model
from state import State
from nodes import (
    fetch_ai_news_rss_node, 
    choose_relevant_article_node,
    select_article_node,
    generate_linkedin_post_node, 
    get_user_feedback_node,
    save_linkedin_post_node
)

# Load environment variables
load_dotenv()

# Determine model name and initialize the LLM
model_name = os.getenv("MODEL", "local")
llm = get_model("ollama/gemma2") if model_name == "local" else get_model("openai/gpt-4o-mini")

def get_timestamp() -> str:
    """Get current timestamp in HH:MM:SS format."""
    return datetime.now().strftime("%H:%M:%S")

def print_with_timestamp(message: str) -> None:
    """Print a message with current timestamp."""
    print(f"[{get_timestamp()}] {message}")

def print_step(step_name: str, status: str = "started") -> None:
    """Print the current step with timestamp and status."""
    print_with_timestamp(f"{step_name} - {status}")

def should_gather_more_info(state: State) -> bool:
    """Determine if we need to gather more information."""
    return state.needs_more_info

def should_rewrite_post(state: State) -> bool:
    """Determine if we need to rewrite the post."""
    return state.needs_rewrite

def determine_next_step(state: State) -> str:
    """
    Determine the next step based on the quality evaluation results.
    
    Returns:
        str: Name of the next node to execute
    """
    if state.needs_rewrite:
        return "generate_linkedin_post"
    else:
        return "save_linkedin_post"

def build_workflow() -> StateGraph:
    """
    Build and configure the workflow graph.
    
    Returns:
        Compiled workflow graph
    """
    # Initialize graph builder
    builder = StateGraph(State)

    # Add nodes
    builder.add_node("fetch_ai_news_rss_node", fetch_ai_news_rss_node)
    builder.add_node("choose_relevant_article", choose_relevant_article_node)
    builder.add_node("select_article", select_article_node)
    builder.add_node("generate_linkedin_post", generate_linkedin_post_node)
    builder.add_node("get_user_feedback", get_user_feedback_node)
    builder.add_node("save_linkedin_post", save_linkedin_post_node)

    # Add edges to connect nodes
    builder.add_edge(START, "fetch_ai_news_rss_node")
    builder.add_edge("fetch_ai_news_rss_node", "choose_relevant_article")
    builder.add_edge("choose_relevant_article", "select_article")
    builder.add_edge("select_article", "generate_linkedin_post")
    builder.add_edge("generate_linkedin_post", "get_user_feedback")
    
    # Add conditional edges from user feedback
    builder.add_conditional_edges(
        "get_user_feedback",
        determine_next_step,
        {
            "generate_linkedin_post": "generate_linkedin_post",  # Rewrite post if needed
            "save_linkedin_post": "save_linkedin_post"          # Proceed to save if approved
        }
    )
    
    builder.add_edge("save_linkedin_post", END)

    # Compile and return
    return builder.compile()

def main() -> None:
    """
    Main function to execute the workflow and display results.
    """
    print_with_timestamp("\n=== Starting LinkedIn Post Generation Workflow ===\n")
    
    # Build the workflow
    graph = build_workflow()
    
    # Optional: Uncomment to save graph visualization
    with open("graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    # Execute workflow
    initial_state = State(search_results=[], news_articles=[])
    state = graph.invoke(initial_state)
    
    error = state.get('error')
    if error:
        print_with_timestamp(f"\n❌ Workflow failed with error: {error}")
    else:
        print("\n")
        print_with_timestamp("✅ Workflow completed successfully!")
        print_with_timestamp(f"📝 LinkedIn post saved to: linkedin_post.txt")

if __name__ == "__main__":
    main()
