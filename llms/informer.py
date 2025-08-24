from typing import Dict, Any
from langchain_groq import ChatGroq
import json
import os

gpt5_mini = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.environ["GROQ_API_KEY"]
    )

SYSTEM = """Plan an informational reply that optimizes:
maximize(clarity + creativity + confidence) / minimize(cognitive_load + decision_fatigue).
Decide structure, brevity, and optional extras.

Return JSON:
{
  "structure": "bullets" | "numbered" | "short-paragraph" | "qa",
  "tldr": string,                  // ≤ 25 words
  "depth": "quick" | "standard" | "deep",
  "include": {
     "examples": boolean,
     "analogy": boolean,
     "tiny_next_step": boolean     // 1 concrete action if relevant
  },
  "tone": "neutral" | "warm" | "energetic",
  "confidence": 0.0-1.0,           // your certainty about core facts
  "notes": string                  // internal guidance for the drafter
}"""

def plan_inform(user_text:str, summary:str)->Dict[str,Any]:
    user_prompt = f"""User asked: {user_text}
Context summary (optional): {summary or "(none)"}

Pick structure that reduces reading friction. Prefer bullets for lists/definitions;
qa for single Q; short-paragraph for quick historical facts."""
    try:
        txt = gpt5_mini.invoke([("system", SYSTEM), ("user", user_prompt)]).content
        return json.loads(txt)
    except Exception:
        return {
          "structure":"short-paragraph","tldr":"Here’s the gist in one sentence.",
          "depth":"standard","include":{"examples":False,"analogy":False,"tiny_next_step":False},
          "tone":"neutral","confidence":0.7,"notes":"fallback"
        }
