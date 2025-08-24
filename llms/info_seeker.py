from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser, JsonOutputParser
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from models.info_seeker import (
    Document, RefinedQueries, FactCheckResult, SummaryResult, 
    ExplanationResult, ComparisonResult
)
from .llm_factory import get_groq_llm
from prompts.info_seeker_prompts import (
    NORMALIZER_PROMPT, FACT_CHECKER_PROMPT, SUMMARIZER_PROMPT, 
    EXPLAINER_PROMPT, COMPARER_PROMPT, SUPERVISOR_PROMPT
)

def get_web_search_chain() -> Runnable:
    """Returns a chain that invokes the web search tool."""
    llm = get_groq_llm()
    tool = {"type": "web_search_preview"}
    llm_with_tools = llm.bind_tools([tool], tool_choice="web_search_preview")
    return llm_with_tools

def get_normalizer_chain() -> Runnable:
    """Creates a chain that takes a list of documents and extracts key facts, entities, and a timeline."""
    llm = get_groq_llm()
    parser = JsonOutputParser()
    prompt_with_format = NORMALIZER_PROMPT.partial(
        format_instructions="Return a JSON object with 'key_facts', 'entities', and 'timeline' keys."
    )
    return prompt_with_format | llm | parser

def get_fact_checker_chain() -> Runnable:
    """Creates a chain that checks facts and adds confidence scores."""
    llm = get_groq_llm()
    parser = PydanticOutputParser(pydantic_object=FactCheckResult)
    prompt_with_format = FACT_CHECKER_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )
    return prompt_with_format | llm | parser

def get_summarizer_chain() -> Runnable:
    """Creates a chain that synthesizes verified facts into a summary."""
    llm = get_groq_llm()
    parser = PydanticOutputParser(pydantic_object=SummaryResult)
    prompt_with_format = SUMMARIZER_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )
    return prompt_with_format | llm | parser

def get_explainer_chain() -> Runnable:
    """Creates a chain that provides a detailed explanation of the topic."""
    llm = get_groq_llm()
    parser = PydanticOutputParser(pydantic_object=ExplanationResult)
    prompt_with_format = EXPLAINER_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )
    return prompt_with_format | llm | parser

def get_comparer_chain() -> Runnable:
    """Creates a chain that compares and contrasts key points."""
    llm = get_groq_llm()
    parser = PydanticOutputParser(pydantic_object=ComparisonResult)
    prompt_with_format = COMPARER_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )
    return prompt_with_format | llm | parser

class SupervisorOutput(BaseModel):
    """Supervisor's decision on the next agent to call."""
    next_agent: str = Field(description="The name of the next agent to call (e.g., 'retriever', 'normalizer', 'FINISH').")

def get_supervisor_chain() -> Runnable:
    """Creates a chain that routes tasks to the correct agent."""
    llm = get_groq_llm()
    parser = PydanticOutputParser(pydantic_object=SupervisorOutput)

    # Inject the format instructions into the existing prompt
    prompt_with_format = SUPERVISOR_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )

    return prompt_with_format | llm | parser
