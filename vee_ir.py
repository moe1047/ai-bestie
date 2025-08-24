"""
Vee-IR (Information Retriever) — LangGraph single-file implementation (no web)

This file defines a simplified LangGraph agent with a single node for drafting
answers based on provided context.

Key Components:
- State: `VeeIRState` defines the data structure for the graph.
- Nodes: `node_draft_answer` formats context and generates a response.
- Graph: A simple workflow from START to the answer drafting node to END.

Dependencies:
  pip install langgraph langchain langchain-openai python-dotenv

Environment:
  Create a .env file with your OPENAI_API_KEY, or export it.

Usage:
  python vee-irl.py
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict

from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Load environment variables from .env file
load_dotenv()

# ===============================
# System Prompt (No Web)
# ===============================
VEE_IR_PROMPT = (
    "You are **Vee (Assistant Mode)**, the user's information brain.\n"
    "Your job: deliver precise, verifiable answers using ONLY: (1) the conversation turn, (2) pinned context 'Pins', (3) user files/snippets provided in this thread, (4) long-term memory items explicitly supplied in-system, and (5) your model prior (general knowledge) — but clearly marked when used.\n\n"
    "NEVER browse or invent sources. Do not reveal internal chain-of-thought; show conclusions, evidence, and concise calculations only.\n\n"
    "IDENTITY & OBJECTIVES\n"
    "- Be crisp, expert, and pragmatic. Solve the user's info need quickly.\n"
    "- Prioritize correctness, then completeness, then brevity.\n"
    "- When stakes are high (medical, legal, financial, safety), insert a short caution.\n\n"
    "CONTEXT PRIORITY ORDER\n"
    "1) Pins / quoted snippets with metadata\n"
    "2) Files the user attached in this thread\n"
    "3) Long-term memory items explicitly shown to you\n"
    "4) Model prior (general knowledge)\n\n"
    "If sources disagree, prefer newer/dater-stamped and more direct sources (e.g., the actual PDF excerpt) over summaries. If still conflicting, state the conflict and give best-supported conclusion.\n\n"
    "RETRIEVAL & REASONING HEURISTICS (do silently)\n"
    "- Query expansion: internally consider synonyms, acronyms, regional spellings.\n"
    "- Canonicalize entities, dates, units; convert units where helpful.\n"
    "- Temporal sanity checks: ensure timelines make sense; flag possible 'recency risk'.\n"
    "- Definition-first for niche terms; example-first for procedures.\n"
    "- Red-team pass: quickly scan for contradictions, scope creep, and missing constraints.\n\n"
    "WHEN INFORMATION IS MISSING\n"
    "- If the answer materially depends on unknowns, ask one precise question.\n"
    "- Otherwise, proceed with stated assumptions (list them) and offer the next best step.\n\n"
    "STYLE & TONE\n"
    "- Point-first: answer in the first 1–2 sentences.\n"
    "- Use tight bullets, tables, or steps when helpful.\n"
    "- Numbers: include units; show one key calc if relevant.\n"
    "- Jargon only when audience is expert; default to plain English.\n\n"
    "OUTPUT FORMAT (always)\n"
    "**Answer:** <concise, direct answer>\n\n"
    "**Why this is true (evidence):**\n"
    "- <cite Pin/File/Memory label + short justification>\n"
    "- <if using model prior, mark as 'Model prior'>\n\n"
    "**Assumptions & caveats:** <only if any>\n\n"
    "**Confidence:** High | Medium | Low  (brief reason)\n\n"
    "(If useful) **Next steps:** <1–3 high-leverage actions, checks, or formulas>\n\n"
    "SOURCE CITATION RULES\n"
    "- Cite by handle the user can see (e.g., [Pin: 'Q3 Plan', §Objectives], [File: contract_v2.pdf, p.3]).\n"
    "- Do NOT fabricate links or external citations.\n"
    "- When using model prior, label it exactly as **Model prior**.\n\n"
    "SAFETY & HONESTY\n"
    "- If you are not confident or the topic is recency-sensitive, say so and mark as 'recency risk'.\n"
    "- Refuse harmful or disallowed requests and suggest safer alternatives.\n\n"
    "LATENCY & LENGTH\n"
    "Default to 5–9 bullets or ≤200 words unless the user asks for depth."
)


# ===============================
# State Definition
# ===============================
class Citation(TypedDict, total=False):
    """Represents a piece of context with a human-visible handle."""

    kind: Literal["pin", "file", "memory"]  # type/category
    label: str  # e.g., "Q3 Plan", "pricing_test_v2.xlsx", "Hiring prefs"
    section: Optional[str]  # e.g., "§Objectives", "p.3", "Tab: WTP"
    text: str  # the excerpt text to use as evidence
    date: Optional[str]  # ISO date string if relevant for recency


class FinalAnswer(BaseModel):
    """A structured representation of the final answer."""

    answer: str = Field(description="The final, concise answer to the user's query.")
    evidence: List[str] = Field(
        description="A list of citations supporting the answer.", default_factory=list
    )
    assumptions_caveats: Optional[str] = Field(
        None, description="Any assumptions made or caveats to mention."
    )
    confidence: Literal["High", "Medium", "Low"] = Field(
        description="The confidence level in the answer."
    )
    next_steps: Optional[List[str]] = Field(
        None, description="Suggested next steps for the user."
    )


class VeeIRState(TypedDict, total=False):
    """Defines the state for the information retrieval graph."""

    user_query: str
    pins: List[Citation]
    files: List[Citation]
    memories: List[Citation]
    conversation_history: List[SystemMessage | HumanMessage]  # For context
    final_answer: str
    structured_answer: dict  # To store the full structured output


# ===============================
# Utilities
# ===============================
def _trim(text: str, max_chars: int) -> str:
    """Trims text to a maximum number of characters, adding an ellipsis if needed."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3] + "..."


def render_context_block(
    pins: Optional[List[Citation]],
    files: Optional[List[Citation]],
    memories: Optional[List[Citation]],
    max_total_chars: int = 6000,
) -> str:
    """Renders a human-citable context block with labels for the LLM.

    The block is intentionally simple plaintext to ensure portability across providers.
    """
    pins = pins or []
    files = files or []
    memories = memories or []

    def fmt(c: Citation, prefix: str) -> str:
        sec = f", {c['section']}" if c.get("section") else ""
        dt = f" ({c['date']})" if c.get("date") else ""
        header = f"[{prefix}: {c['label']}{sec}]{dt}"
        return f"{header}\n{c['text'].strip()}\n"

    parts: List[str] = []
    if pins:
        parts.append("# Pins\n" + "\n".join(fmt(c, "Pin") for c in pins))
    if files:
        parts.append("# Files\n" + "\n".join(fmt(c, "File") for c in files))
    if memories:
        parts.append("# Memories\n" + "\n".join(fmt(c, "Memory") for c in memories))

    block = "\n\n".join(parts).strip()
    return _trim(block, max_total_chars)


# ===============================
# LLM Client
# ===============================
def make_llm(model: str = "gpt-4o", temperature: float = 0.2) -> ChatOpenAI:
    """Factory for the chat model. Adjust model name and other settings as needed."""
    return ChatOpenAI(model=model, temperature=temperature)


# ===============================
# Graph Nodes
# ===============================
def node_draft_answer(state: VeeIRState) -> VeeIRState:
    """Formats context and drafts a structured answer in a single step."""
    context_block = render_context_block(
        state.get("pins"), state.get("files"), state.get("memories")
    )

    # Bind the Pydantic model to the LLM for structured output
    llm = make_llm().with_structured_output(FinalAnswer)

    history = state.get("conversation_history", [])

    messages = [
        SystemMessage(content=VEE_IR_PROMPT),
        *history,
        HumanMessage(
            content=(
                "Use ONLY the following context, the user's question, and if necessary your model prior (but label it).\n\n"
                f"=== CONTEXT START ===\n{context_block}\n=== CONTEXT END ===\n\n"
                f"User question:\n{state['user_query']}"
            )
        ),
    ]

    # Get the structured response from the LLM
    structured_response: FinalAnswer = llm.invoke(messages)

    # Store the full structured answer and the final text answer in the state
    state["structured_answer"] = structured_response.dict()
    state["final_answer"] = structured_response.answer
    return state


# ===============================
# Graph Assembly
# ===============================
def build_graph() -> StateGraph:
    """Builds the LangGraph state machine."""
    graph = StateGraph(VeeIRState)
    graph.add_node("draft_answer_node", node_draft_answer)
    graph.add_edge(START, "draft_answer_node")
    graph.add_edge("draft_answer_node", END)
    return graph


# ===============================
# Example Runner
# ===============================
if __name__ == "__main__":
    # Compile the graph into a runnable application
    app = build_graph().compile()

    # Define an example state to run the graph with
    example_state: VeeIRState = {
        "user_query": "Explain what is AI. explain in detail please ?",
        "pins": [],
        "files": [],
        "memories": [],
    }

    # Invoke the graph with the example state
    output: VeeIRState = app.invoke(example_state)

    # Print the final answer
    print("==== FINAL ANSWER ====")
    print(output.get("final_answer", "<no answer>"))
    print("\n==== STRUCTURED ANSWER (JSON) ====")
    print(json.dumps(output.get("structured_answer", {}), indent=2))
