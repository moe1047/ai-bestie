import re

def format_for_telegram(text: str) -> str:
    """Converts simple markdown to Telegram-compatible HTML."""
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Convert [links](url) to <a href="url">links</a>
    text = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2">\1</a>', text)

    return text
