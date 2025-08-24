from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from prompts.omni_responder_prompt import OMNI_RESPONDER_PROMPT
from .llm_factory import get_groq_llm

def get_omni_responder_chain() -> Runnable:
    """Create the chain for the OmniResponder."""
    llm = get_groq_llm(temperature=0.7)  # Using higher temperature for more creative responses
    return OMNI_RESPONDER_PROMPT | llm | StrOutputParser()
