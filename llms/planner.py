import os
from typing import Dict, Any
import json
from dotenv import load_dotenv
from langchain.output_parsers import PydanticOutputParser
from .llm_factory import get_groq_llm

# Load environment variables
load_dotenv()

# Import the correct, mode-specific prompts
from graph.vee_ir import load_prompt
from langchain_core.prompts import ChatPromptTemplate
from models.planning import ConversationStrategy

def get_planning_chain():
    """Creates the planning chain for the Bestie persona."""
    prompt_template = load_prompt('bestie/planner_prompt.md')
    prompt = ChatPromptTemplate.from_template(prompt_template)
    print("---USING BESTIE PLANNER (prompts/bestie/planner_prompt.md)---")

    model = get_groq_llm(model_name="moonshotai/kimi-k2-instruct")
    parser = PydanticOutputParser(pydantic_object=ConversationStrategy)

    return prompt | model | parser

def plan_next_move(sensing: Dict[str, Any], conversation_history: str, user_name: str, user_context: str) -> Dict[str, Any]:
    """Plans the next conversational move for the Bestie persona."""
    planning_chain = get_planning_chain()
    
    input_data = {
        "sensing_data": json.dumps(sensing, indent=2),
        "conversation_history": conversation_history or "(none)",
        "user_name": user_name,
        "user_context": user_context
    }

    try:
        result = planning_chain.invoke(input_data)
        return result.model_dump()
    except Exception as e:
        print(f"Error in plan_next_move: {e}")
        # Fallback response
        return {
            "strategy_note": "Default to a gentle, open-ended response due to an error.",
            "response_components": [
                {"type": "validate", "focus": "the user's feelings"},
                {"type": "ask_open_question", "focus": "how they are doing"}
            ]
        }
