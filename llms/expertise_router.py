from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser

from prompts.expertise_router_prompt import EXPERTISE_ROUTER_PROMPT
from .llm_factory import get_groq_llm

def get_expertise_router_chain() -> Runnable:
    """Create the chain for the expertise router."""
    llm = get_groq_llm(temperature=0)
    return EXPERTISE_ROUTER_PROMPT | llm | StrOutputParser()
