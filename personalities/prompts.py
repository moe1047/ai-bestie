from pathlib import Path

def get_gentle_listener_prompt() -> str:
    """Loads the Gentle Listener persona prompt from the markdown file."""
    prompt_path = Path(__file__).parent / "gentle_listener.md"
    return prompt_path.read_text()
