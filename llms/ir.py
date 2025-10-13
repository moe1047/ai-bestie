import json
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from .llm_factory import get_groq_llm
from models.vee_ir import UnifiedGoal, Plan
from utils.file_io import load_prompt

# Load Prompts
CLASSIFIER_PROMPT = load_prompt("vee_ir/classifier_prompt.md")
UNIFIED_GOAL_EXTRACTOR_PROMPT = load_prompt("vee_ir/unified_goal_extractor_prompt.md")
PLANNER_PROMPT = load_prompt("vee_ir/planner_prompt.md")
KNOWLEDGE_GENERATOR_PROMPT = load_prompt("vee_ir/knowledge_generator_prompt.md")

def classify_intent(conversation_history: str, user_query: str) -> dict:
    """Classifies the user's information-seeking intent."""
    llm = get_groq_llm(model_name="llama3-8b-8192")
    prompt_input = f"""Conversation History:
{conversation_history}

Latest user message: {user_query}"""
    
    prompt = f"{CLASSIFIER_PROMPT}\n\n{prompt_input}"
    response = llm.invoke(prompt)
    
    try:
        return json.loads(response.content.strip())
    except (json.JSONDecodeError, KeyError):
        return {
            "intent": "Learn",
            "reasoning": "Fallback due to parsing error.",
        }

def extract_goal(conversation_history: str, user_query: str, user_intent: str) -> dict:
    """Extracts the user's goal and breaks it down into sub-tasks."""
    llm = get_groq_llm(model_name="llama3-8b-8192")
    prompt = UNIFIED_GOAL_EXTRACTOR_PROMPT.format(
        conversation_history=conversation_history,
        user_query=user_query,
        user_intent=user_intent,
    )

    parser = PydanticOutputParser(pydantic_object=UnifiedGoal)

    try:
        response = llm.invoke(prompt)
        goal_data = parser.parse(response.content)
        return goal_data.model_dump()
    except Exception as e:
        print(f"Error: Could not parse unified goal from LLM response: {e}")
        return {
            "goal": "Fallback Goal",
            "sub_tasks": [],
            "clarification_needed": True,
            "missing_info": ["Could not process request."],
        }

def plan_ir_response(conversation_history: str, user_query: str, user_intent: str, goal: str, sub_tasks: str) -> dict:
    """Creates a plan for the information retrieval response."""
    llm = get_groq_llm(model_name="llama3-8b-8192")
    prompt = PLANNER_PROMPT.format(
        conversation_history=conversation_history,
        user_query=user_query,
        user_intent=user_intent,
        goal=goal,
        sub_tasks=sub_tasks,
    )

    parser = PydanticOutputParser(pydantic_object=Plan)

    try:
        response = llm.invoke(prompt)
        plan_data = parser.parse(response.content)
        return plan_data.model_dump()
    except Exception as e:
        print(f"Error: Could not parse plan from LLM response: {e}")
        return {
            "note": "Fallback plan due to a parsing error.",
            "tasks": [],
            "clarification_needed": True,
            "missing_info": ["Could not process the planning step."],
        }

def generate_knowledge(conversation_history: str, plan: str) -> str:
    """Generates the final, synthesized answer based on the plan."""
    llm = get_groq_llm(model_name="llama3-70b-8192")
    prompt = KNOWLEDGE_GENERATOR_PROMPT.format(
        conversation_history=conversation_history,
        plan=plan,
    )
    
    response = llm.invoke(prompt).content
    return response
