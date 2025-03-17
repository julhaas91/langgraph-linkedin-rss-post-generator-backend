import os
from langchain_openai import ChatOpenAI
from langchain_google_vertexai import ChatVertexAI
from langchain_ollama import ChatOllama

from dotenv import load_dotenv
load_dotenv()

def get_model(model_name: str):
    """
    Get the model instance based on the model_name.
    Args:
        model_name (str): The model id in the format of "{provider}/{model}".
    Returns:
        ChatModel: The model instance.
    """
    provider, model = model_name.split("/")

    if provider == "ollama":
        return ChatOllama(
            model=model, # e.g. "gemma2"
            base_url="http://localhost:11434",
            num_ctx=8192,
        )
    
    if provider == "openai":
        return ChatOpenAI(
            model_name=model, # e.g. "gpt-4o-mini"
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=os.environ["OPENAI_API_KEY"]
    )

    if provider == "google":
        return ChatVertexAI(
        model=model, # e.g. "gemini-2.-flash"
        temperature=0,
        max_tokens=None,
        max_retries=6,
        stop=None
    )

    else:
        raise ValueError(f"Model type '{type}' is not supported.")
    