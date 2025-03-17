"""
AI News Workflow that fetches, filters, and creates LinkedIn posts.

This module creates a workflow that:
1. Searches the web for the latest AI news
2. Selects a relevant article based on predefined criteria
3. Generates a LinkedIn post about the selected article

Based on https://langchain-ai.github.io/langgraph/tutorials/workflows/
"""

import os

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from models import get_model
from state import State
from nodes import fetch_ai_news_rss_node, choose_relevant_article_node, generate_linkedin_post_node, save_linkedin_post_node

# Load environment variables
load_dotenv()

# Determine model name and initialize the LLM
model_name = os.getenv("MODEL", "local")
llm = get_model("ollama/gemma2") if model_name == "local" else get_model("openai/gpt-4o-mini")



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
    builder.add_node("generate_linkedin_post", generate_linkedin_post_node)
    builder.add_node("save_linkedin_post", save_linkedin_post_node)

    # Add edges to connect nodes
    builder.add_edge(START, "fetch_ai_news_rss_node")
    builder.add_edge("fetch_ai_news_rss_node", "choose_relevant_article")
    builder.add_edge("choose_relevant_article", "generate_linkedin_post")
    builder.add_edge("generate_linkedin_post", "save_linkedin_post")
    builder.add_edge("save_linkedin_post", END)

    # Compile and return
    return builder.compile()


def main() -> None:
    """
    Main function to execute the workflow and display results.
    """
    # Build the workflow
    graph = build_workflow()
    
    # Optional: Uncomment to save graph visualization
    with open("graph.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    # Execute workflow
    initial_state = State(search_results=[], news_articles=[])
    state = graph.invoke(initial_state)
    print("Workflow completed successfully.")

if __name__ == "__main__":
    main()
