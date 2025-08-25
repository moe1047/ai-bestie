from langchain_groq import ChatGroq
from typing import Dict
import json

from .llm_factory import get_groq_llm

# Replace OpenAI moderation with Groq
groq_mod = get_groq_llm(temperature=0, json_mode=True)
llama_guard = ChatGroq(model="llama-3.1-8b-instant", temperature=0, json_mode=True)

def safety_triage(text:str)->Dict:
    try:
        mod = groq_mod.invoke([('system',"Classify risk 0-3 and reasons as JSON."),
                                 ("user", f"Message:\n{text}\nReturn JSON {{risk_level:0..3, reasons:[...]}}")]).content
        data = json.loads(mod)
    except Exception:
        data = {"risk_level":0, "reasons":["parse_fail"]}

    try:
                # Define the safety policy for the general-purpose model
        safety_policy = """You are a content moderator. Your task is to determine if the user's text violates any of the following policies:
- Hate Speech: Content that promotes violence, incites hatred, promotes discrimination, or disparages on the basis of race or ethnic origin, religion, disability, age, nationality, veteran status, sexual orientation, sex, gender, gender identity, caste, immigration status or any other characteristic that is associated with systemic discrimination or marginalization.
- Harassment: Content that is abusive, threatening, or insulting.
- Self-Harm: Content that encourages or provides instructions on how to self-harm or commit suicide.
- Sexual Content: Content that contains nudity, sexually explicit acts, or is otherwise pornographic.
- Violence: Content that depicts, encourages, or helps others to commit acts of violence.

Analyze the user's text and respond ONLY with a JSON object containing two keys:
1. "flag": A boolean value. Set to `true` if the text violates any policy, otherwise `false`.
2. "reasons": A list of strings explaining which policies were violated. If no policies were violated, provide an empty list.

Be conservative in your judgment. If you are unsure, err on the side of caution and flag the content."""

        guard = llama_guard.invoke([
            ("system", safety_policy),
            ("user", f"User text to analyze: {text}")
        ]).content
        g = json.loads(guard)
    except Exception:
        g = {"flag": False, "reasons":["parse_fail"]}

    risk = max(int(data.get("risk_level",0)), 3 if g.get("flag") else 0)
    
    return {"risk_level": risk, "openai": data, "guard": g}
