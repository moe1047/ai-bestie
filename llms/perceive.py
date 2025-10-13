from typing import Dict, Any
from langchain_groq import ChatGroq
import json
from pathlib import Path
from datetime import datetime, timezone
from langchain_core.output_parsers import JsonOutputParser

# Use the model specified by the user
groq_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

USER_PROMPT_TEMPLATE = """<context:inputs>
{context_json}
</context:inputs>"""

def _get_system_prompt() -> str:
    """Loads the system prompt from the markdown file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "perceive.md"
    return prompt_path.read_text()

def _get_default_perception() -> Dict[str, Any]:
    """Returns a default perception object for error cases."""
    return {
        "meta": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "channel": "text",
            "is_follow_up": False
        },
        "discourse": {
            "dialogue_act": ["chitchat"]
        },
        "intent": {
            "primary": "socialize",
            "sub": "default due to error",
            "conf": {"primary": 0.5, "sub": 0.5}
        },
        "entities": [],
        "affect": {
            "sentiment": "neutral",
            "valence": 0.0,
            "arousal": 0.0,
            "emotion_probs": {"neutral": 1.0},
            "confidence": 0.5
        },
        "safety": {
            "risk_level": "none",
            "distress_hint": False
        },
        "pragmatics": {
            "inference": "Default perception due to an internal error.",
            "needs_clarification": True,
            "sarcasm_possible": False
        },
    }

def perceive(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the provided context using the Vee Sense model to generate a detailed perception JSON.

    Args:
        context: A dictionary containing the full context required by the perception prompt,
                 including latest_message, conversation_history, user_profile, etc.

    Returns:
        A dictionary conforming to the 'Tiny Perception v1.1' schema.
    """
    system_prompt = _get_system_prompt()
    user_prompt = USER_PROMPT_TEMPLATE.format(context_json=json.dumps(context, indent=2))
    parser = JsonOutputParser()

    try:
        response = groq_fast.invoke(
            [   ("system", system_prompt),
                ("user", user_prompt)
            ]
        )
        return parser.parse(response.content)
    except (json.JSONDecodeError, Exception) as e:
        # In a real application, you'd want to log this error and the invalid response content.
        print(f"Error during perception generation: {e}")
        # Return a safe, default perception object that matches the required schema.
        return _get_default_perception()
