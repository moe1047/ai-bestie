import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string
from langchain_core.pydantic_v1 import BaseModel, Field
from .llm_factory import get_groq_llm


class ModeDecision(BaseModel):
    """The structured output for the mode decider."""
    mode: str = Field(description="One of 'Bestie', 'InformationGuardian', or 'Refusal'")
    rationale: str = Field(description="A short reason for the mode choice.")
    ask_clarifying_question: bool = Field(default=False)


def decide_mode(
    intent: Dict[str, Any],
    conversation_history: List[HumanMessage | AIMessage],
    mode_history: List[str],
) -> Dict[str, Any]:
    """Analyzes user input and decides the interaction mode."""
    parser = JsonOutputParser(pydantic_object=ModeDecision)

    prompt_path = Path(__file__).parent.parent / "prompts" / "mode_decider.md"
    prompt_template = prompt_path.read_text()
    prompt = ChatPromptTemplate.from_template(
        prompt_template,
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    llm = get_groq_llm(model_name="llama3-8b-8192", temperature=0.0)
    chain = prompt | llm | parser

    history_str = get_buffer_string(conversation_history)
    last_mode = mode_history[-1] if mode_history else "None"

    try:
        result = chain.invoke({
            "intent_json": json.dumps(intent, indent=2),
            "conversation_history": history_str,
            "last_mode": last_mode,
        })
        return result
    except Exception as e:
        print(f"Error in mode decider: {e}")
        return {
            "mode": "Bestie",
            "rationale": "Defaulted to Bestie mode due to an internal error.",
            "ask_clarifying_question": True,
        }


def get_mode_decider_chain():
    """DEPRECATED: Creates a chain to decide the interaction mode."""
    # This function is kept for compatibility but should be phased out.
    pass
