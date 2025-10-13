from typing import Dict, Any, List
from langchain_groq import ChatGroq
import json

EMOTION_SCHEMA = {
    "type": "object",
    "properties": {
        "emotions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "score": {"type": "number"},
                },
            },
        },
        "uncertainty": {"type": "number"},
    },
    "required": ["emotions", "uncertainty"],
}

groq_fast = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

def detect_emotion(text: str, recent: List[Dict[str, str]]) -> Dict[str, Any]:
    ctx = "\n".join(f"{m['role']}: {m['content']}" for m in recent[-3:])
    prompt = f"""Return compact JSON only, matching this schema:
{json.dumps(EMOTION_SCHEMA, indent=2)}

Recent turns:
{ctx}

User: {text}

Infer up to 3 emotions (0..1) from the user's last message."""
    try:
        out = groq_fast.invoke(
            [("system", "You are a precise emotion detector."), ("user", prompt)]
        ).content
        return json.loads(out)
    except Exception:
        return {
            "emotions": [],
            "uncertainty": 0.8,
        }
