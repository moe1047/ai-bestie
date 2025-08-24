from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from prompts.mode_decider_prompt import MODE_DECIDER_PROMPT
from .llm_factory import get_groq_llm

def get_mode_decider_chain() -> Runnable:
    """Create the chain for the mode decider."""
    llm = get_groq_llm(temperature=0)
    return MODE_DECIDER_PROMPT | llm | StrOutputParser()
