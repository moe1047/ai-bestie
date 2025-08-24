import os
from typing import Dict, Any, Literal
from dotenv import load_dotenv
from langchain.output_parsers import PydanticOutputParser
from .llm_factory import get_groq_llm

# Load environment variables
load_dotenv()

# Import the correct, mode-specific prompts
from prompts.select_strategy_prompt import select_strategy_prompt
from prompts.assistant_planner_prompt import assistant_planner_prompt
from models.planning import PlanningResult, ConversationStrategy

def get_planning_chain(mode: Literal["bestie", "assistant"]):
    """Create a mode-aware planning chain with Groq LLM."""
    if mode == "bestie":
        prompt = select_strategy_prompt
        print("---USING BESTIE PLANNER (Vee's Heart & Mind)---")
    else:  # assistant mode
        prompt = assistant_planner_prompt
        print("---USING ASSISTANT PLANNER---")

    model = get_groq_llm()
    if mode == "bestie":
        parser = PydanticOutputParser(pydantic_object=ConversationStrategy)
    else: # assistant
        parser = PydanticOutputParser(pydantic_object=PlanningResult)

    chain = prompt | model | parser
    return chain

def plan_next_move(mode: str, sensing: Dict[str, Any], conversation_history: str, latest_user_message: str) -> Dict[str, Any]:
    """Plan the next conversation move based on the selected mode."""
    planning_chain = get_planning_chain(mode)
    
    # Prepare inputs based on the mode
    if mode == "bestie":
        input_data = {
            "sensing": sensing,
            "conversation_history": conversation_history or "(none)"
        }
    else: # assistant
        input_data = {
            "latest_user_message": latest_user_message,
            "conversation_history": conversation_history or "(none)"
        }

    try:
        result = planning_chain.invoke(input_data)
        return result.model_dump()
    except Exception as e:
        print(f"Error in plan_next_move: {e}")
        # Fallback response
        high_emotion = (sensing.get("uncertainty", 0) > 0.45) or \
                      any(e.get("score", 0) > 0.75 for e in sensing.get("emotions", []))
        return {
            "strategy": "reflect",
            "question": None,
            "high_emotion": high_emotion,
            "notes": "Error in planning - using fallback strategy"
        }
