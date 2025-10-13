from typing import Dict, Any
import json
from langchain_groq import ChatGroq
from pathlib import Path
from langchain_core.output_parsers import JsonOutputParser
from models.plan import VeePlan

# Use the model specified by the user
# Use the model specified by the user
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)
USER_PROMPT_TEMPLATE = """<context:inputs>
{context_json}
</context:inputs>"""

def _get_system_prompt() -> str:
    """Loads the system prompt from the markdown file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "plan.md"
    return prompt_path.read_text()

def _get_default_plan() -> Dict[str, Any]:
    """Returns a default plan object for error cases."""
    return {
        "plan": {
            "goal_type": "self_reflect",
            "blocks": {
                "opening": "Acknowledge the user's message and validate their feelings.",
                "core": "Ask a gentle, open-ended question to encourage reflection.",
                "micro_plan": [],
                "close": "Offer support and reaffirm that you're there to listen.",
                "safety_bridge": None
            },
            "offer": {
                "type": "affirmation",
                "content": "Reassure the user that their feelings are valid."
            },
            "style": {
                "tone": "warm",
                "pacing": "medium",
                "emoji_style": "soft",
                "word_limit": 80,
                "budget": {"opening": 25, "core": 35, "close": 20, "micro_plan": 0}
            },
            "notes": "Default plan due to an internal error. Focus on safety, validation, and open-ended support."
        }
    }

def plan(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a conversational plan based on the reasoning output and current state.

    Args:
        context: A dictionary containing the full context required by the planner prompt.

    Returns:
        A dictionary conforming to the VeePlan schema.
    """
    system_prompt = _get_system_prompt()
    user_prompt = USER_PROMPT_TEMPLATE.format(context_json=json.dumps(context, indent=2))
    parser = JsonOutputParser(pydantic_object=VeePlan)

    try:
        response = llm.invoke(
            [   ("system", system_prompt),
                ("user", user_prompt)
            ]
        )
        return parser.parse(response.content)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error during plan generation: {e}")
        return _get_default_plan()
