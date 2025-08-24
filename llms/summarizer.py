from langchain_groq import ChatGroq

# cheap, very fast rolling summary; ~150-200 tokens
groq_sum = ChatGroq(model="llama3-8b-8192", temperature=0)

SYSTEM = """Summarize the conversation so far in 2–4 bullet points, focusing on:
- user goals, preferences, constraints
- named feelings (granular)
- unresolved questions or next steps
Be neutral, <200 tokens. No fluff."""

def summarize(history_text:str)->str:
    prompt = f"Conversation excerpts:\n{history_text}\n\nReturn a compact bullet summary."
    return groq_sum.invoke([( "system", SYSTEM), ("user", prompt)]).content
