from typing import Dict, Any, List
from langchain_groq import ChatGroq
import json

SENSING_SCHEMA = {
  "type":"object",
  "properties":{
    "emotions":{"type":"array","items":{"type":"object","properties":{
      "label":{"type":"string"},"score":{"type":"number"}}}},
    "intent":{"type":"object","properties":{
      "label":{"type":"string"},"confidence":{"type":"number"}}},
    "uncertainty":{"type":"number"},
    "needs":{"type":"array","items":{"type":"string"}}
  },
  "required":["emotions","intent","uncertainty"]
}

groq_fast = ChatGroq(model="llama3-8b-8192", temperature=0)

def sense(text:str, summary:str, recent:List[Dict[str,str]])->Dict[str,Any]:
    ctx = "\n".join(f"{m['role']}: {m['content']}" for m in recent[-3:])
    prompt = f"""Return compact JSON only, matching this schema:
{SENSING_SCHEMA}

Context summary: {summary or '(none)'}
Recent turns:
{ctx}

User: {text}

Infer up to 3 emotions (0..1), a single top intent, uncertainty (0..1), and 1-3 likely needs."""
    try:
        out = groq_fast.invoke([("system","You are a precise emotion/intent detector."),
                                ("user", prompt)]).content
        return json.loads(out)
    except Exception:
        return {"emotions":[{"label":"uncertain","score":0.5}],
                "intent":{"label":"misc","confidence":0.5},
                "uncertainty":0.6, "needs":[]}
