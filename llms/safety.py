from langchain_groq import ChatGroq
from typing import Dict
import json

from .llm_factory import get_groq_llm

# Replace OpenAI moderation with Groq
groq_mod = get_groq_llm(temperature=0, json_mode=True)
llama_guard = ChatGroq(model="llama-guard-3-8b", temperature=0)

def safety_triage(text:str)->Dict:
    try:
        mod = groq_mod.invoke([('system',"Classify risk 0-3 and reasons as JSON."),
                                 ("user", f"Message:\n{text}\nReturn JSON {{risk_level:0..3, reasons:[...]}}")]).content
        data = json.loads(mod)
    except Exception:
        data = {"risk_level":0, "reasons":["parse_fail"]}

    try:
        guard = llama_guard.invoke([("system","Return JSON {flag: bool, reasons:[...]}. Be conservative."),
                                    ("user", text)]).content
        g = json.loads(guard)
    except Exception:
        g = {"flag": False, "reasons":["parse_fail"]}

    risk = max(int(data.get("risk_level",0)), 3 if g.get("flag") else 0)
    
    return {"risk_level": risk, "openai": data, "guard": g}
