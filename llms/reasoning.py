from typing import Dict, Any
from langchain_groq import ChatGroq
import json
from pathlib import Path
from langchain_core.output_parsers import JsonOutputParser

# Use the model specified by the user
# Use the model specified by the user
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.1)

USER_PROMPT_TEMPLATE = """<context:inputs>
{context_json}
</context:inputs>"""

def _get_system_prompt() -> str:
    """Loads the system prompt from the markdown file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "reasoning.md"
    return prompt_path.read_text()

def _get_default_reasoning() -> Dict[str, Any]:
    """Returns a default reasoning object for error cases."""
    return {
        "rationale": {
            "summary": "Default reasoning due to an internal error. The system will proceed with a safe, gentle response.",
            "evidence": {
                "perception_refs": [],
                "context_refs": []
            },
            "conflicts_or_uncertainty": "High uncertainty due to processing error."
        },
        "context": {
            "is_follow_up": False,
            "subject": "unknown",
            "continuity_hint": "new_thread",
            "last_micro_goal": None,
            "open_loops": []
        },
        "need": {
            "category": "connection",
            "description": "Defaulting to a simple, connecting interaction."
        },
        "micro_goal": {
            "type": "self_reflect",
            "success_hint": "A moment of calm reflection.",
            "time_horizon": "immediate"
        },
        "style_dials": {
            "mode": "Bestie",
            "empathy": 0.7,
            "playfulness": 0.2,
            "evidence": 0.0,
            "tone": "warm",
            "word_limit": 80,
            "pacing": "medium",
            "mirroring_density": "medium"
        }
    }

def reason(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the provided context using the Vee Reasoning model to generate a detailed reasoning JSON.

    Args:
        context: A dictionary containing the full context required by the reasoning prompt,
                 including perception, user_profile, latest_user_message, and last_10_turns.

    Returns:
        A dictionary conforming to the reasoning output schema.
    """
    system_prompt = _get_system_prompt()
    user_prompt = USER_PROMPT_TEMPLATE.format(context_json=json.dumps(context, indent=2))
    parser = JsonOutputParser()

    try:
        response = llm.invoke(
            [   ("system", system_prompt),
                ("user", user_prompt)
            ]
        )
        return parser.parse(response.content)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Error during reasoning generation: {e}")
        return _get_default_reasoning()
