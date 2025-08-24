import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_groq_llm(temperature: float = 0.0, json_mode: bool = False) -> ChatGroq:
    """Factory function to get a configured Groq LLM instance."""
    model_name = "llama-3.3-70b-versatile"
    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}
    
    return ChatGroq(
        model=model_name,
        temperature=temperature,
        groq_api_key=os.environ["GROQ_API_KEY"],
        model_kwargs=model_kwargs
    )
