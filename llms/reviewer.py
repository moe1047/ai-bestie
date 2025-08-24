from langchain_core.prompts import ChatPromptTemplate
from .llm_factory import get_groq_llm

BESTIE_REVIEWER_SYSTEM_PROMPT = """You are a compassionate reviewer ensuring a message written by an AI best friend is perfect. Your goal is to check the draft against the C.A.R.E. principles: Clarity, Accuracy, Relevance, and Empathy. Respond with a JSON object containing:
- 'C': A score from 0.0 to 1.0 for Clarity.
- 'A': A score from 0.0 to 1.0 for Accuracy.
- 'R': A score from 0.0 to 1.0 for Relevance.
- 'E': A score from 0.0 to 1.0 for Empathy.
- 'suggestion': If any score is below 0.7, provide a revised, improved version of the draft. Otherwise, return null.
"""

ASSISTANT_REVIEWER_SYSTEM_PROMPT = """You are a meticulous editor reviewing a draft written by an AI assistant. Your goal is to ensure the draft is clear, factually accurate, and maintains a neutral, helpful tone. Respond with a JSON object containing:
- 'clarity': A score from 0.0 to 1.0 for how clear and easy to understand the draft is.
- 'accuracy': A score from 0.0 to 1.0 for the factual correctness of the information.
- 'neutrality': A score from 0.0 to 1.0 for how neutral and unbiased the tone is.
- 'suggestion': If any score is below 0.8, provide a revised, improved version of the draft. Otherwise, return null.
"""

def get_review_prompt(system_prompt):
    return ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{draft}")
    ])

def review_bestie_draft(draft: str) -> dict:
    """Reviews a bestie draft for quality and returns a C.A.R.E. score."""
    prompt = get_review_prompt(BESTIE_REVIEWER_SYSTEM_PROMPT)
    chain = prompt | get_groq_llm(json_mode=True)
    return chain.invoke({"draft": draft})

def review_assistant_draft(draft: str) -> dict:
    """Reviews an assistant draft for clarity, factuality, and neutrality."""
    prompt = get_review_prompt(ASSISTANT_REVIEWER_SYSTEM_PROMPT)
    chain = prompt | get_groq_llm(json_mode=True)
    return chain.invoke({"draft": draft})
