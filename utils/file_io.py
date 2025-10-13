import os

def load_prompt(file_name: str) -> str:
    """Loads a prompt from the prompts directory."""
    # Assumes this script is called from the project root.
    # The path is relative to the root.
    prompt_path = os.path.join("prompts", file_name)
    try:
        with open(prompt_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: Prompt file '{file_name}' not found."
