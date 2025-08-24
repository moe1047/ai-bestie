from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable

from prompts.assistant_drafter_prompt import ASSISTANT_DRAFTER_PROMPT
from .llm_factory import get_groq_llm

def get_assistant_drafter_chain() -> Runnable:
    """Creates a chain that rewrites an expert draft into the assistant's persona."""
    llm = get_groq_llm(temperature=0.7)  # Using higher temperature for more creative responses
    parser = StrOutputParser()
    chain = ASSISTANT_DRAFTER_PROMPT | llm | parser
    return chain.with_types(input_type={"conversation_history": list, "expert_draft": str})
