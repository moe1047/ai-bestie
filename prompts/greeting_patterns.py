"""Defines greeting patterns for our emotionally attuned AI bestie."""

GREETING_PATTERNS = {
    "hi": ["heyyy bestie! 💫", "hi! how's your day going? 🌟", "hey there! ready to chat? 💖"],
    "hello": ["heyyy! so good to hear from you 💫", "hi bestie! what's on your mind? 🌟", "hello! how are you feeling? 💖"],
    "hey": ["hey bestie! 💫", "heyyy! what's happening? 🌟", "hi! i'm here for you 💖"],
    "sup": ["heyyy! what's new? 💫", "hey bestie! how's everything? 🌟", "hi! what's on your mind? 💖"],
    "yo": ["heyyy bestie! 💫", "yo! how are you? 🌟", "hey! what's happening? 💖"],
    "heyy": ["heyyy! missed you! 💫", "hi bestie! how's your day? 🌟", "hey! so glad you're here 💖"]
}

def is_simple_greeting(message: str) -> bool:
    """Check if a message is a simple greeting that doesn't need deep analysis."""
    message = message.lower().strip()
    return (
        message in GREETING_PATTERNS
        or any(message.startswith(key) for key in GREETING_PATTERNS)
        and len(message.split()) <= 2
    )

def get_greeting_response(message: str) -> str:
    """Get a casual, friendly response for a simple greeting."""
    message = message.lower().strip()
    # Get the base greeting type
    greeting_type = next(
        (key for key in GREETING_PATTERNS if message.startswith(key)),
        "hi"  # default to "hi" patterns if no match
    )
    
    # Get responses for this type of greeting
    responses = GREETING_PATTERNS[greeting_type]
    
    # Use timestamp to select a response (ensures variety)
    from datetime import datetime
    index = int(datetime.now().timestamp()) % len(responses)
    return responses[index]
