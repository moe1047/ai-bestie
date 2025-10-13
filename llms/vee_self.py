from typing import Dict, Any
from langchain_groq import ChatGroq
import json
from pathlib import Path

# Use the model specified by the user
groq_fast = ChatGroq(model="moonshotai/kimi-k2-instruct-0905", temperature=0)

USER_PROMPT_TEMPLATE = """<context:inputs>
{context_json}
</context:inputs>"""

def _get_system_prompt() -> str:
    """Loads the system prompt from the markdown file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "vee_self.md"
    return prompt_path.read_text()

def reply(context: Dict[str, Any]) -> str:
    """
    Generates an AI reply based on the provided context using the Vee Self model.

    Args:
        context: A dictionary containing the full context required by the vee_self prompt.

    Returns:
        A string containing the AI's reply.
    """
    system_prompt = _get_system_prompt()
    user_prompt = USER_PROMPT_TEMPLATE.format(context_json=json.dumps(context, indent=2))

    try:
        response = groq_fast.invoke(
            [   ("system", system_prompt),
                ("user", user_prompt)
            ]
        )
        return response.content
    except Exception as e:
        print(f"Error during vee_self generation: {e}")
        return "I'm not sure how to respond to that."
