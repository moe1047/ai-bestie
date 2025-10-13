from typing import Dict, Any
import json
from langchain_groq import ChatGroq
from pathlib import Path

# Use the model specified by the user
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.1)

USER_PROMPT_TEMPLATE = """<context:inputs>
{context_json}
</context:inputs>"""

def _get_system_prompt() -> str:
    """Loads the system prompt from the markdown file."""
    prompt_path = Path(__file__).parent.parent / "prompts" / "say.md"
    return prompt_path.read_text()

def say(context: Dict[str, Any]) -> str:
    """
    Generates the final response based on the plan and other context.

    Args:
        context: A dictionary containing the full context required by the say prompt.

    Returns:
        The final response as a string.
    """
    system_prompt = _get_system_prompt()
    user_prompt = USER_PROMPT_TEMPLATE.format(context_json=json.dumps(context, indent=2))

    try:
        response = llm.invoke(
            [   ("system", system_prompt),
                ("user", user_prompt)
            ]
        )
        return response.content
    except Exception as e:
        print(f"Error during say generation: {e}")
        return "I'm not sure how to respond to that. Could you try rephrasing?"
