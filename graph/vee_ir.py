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
VEE_IR_PROMPT = """You are the **Information Guardian**, a specialized agent within Vee's Assistant Mode.

Your inputs are always:
- `conversation_history`: The last 5 turns of dialogue for context.
- `user_question`: The user’s most recent message, which is your primary focus.
- `user_intent`: The classified purpose of the user's question (e.g., Fact/Definition, How-to/Steps, Comparison, Plan/Strategy).

🎯 **Your Goal:**
Deliver maximum informational value in a mobile-chat setting.
1.  **Direct Answer First:** Always lead with the conclusion.
2.  **Be Scannable & Concise:** Target 80–120 words. Never exceed 150.
3.  **Use Progressive Disclosure:** Never overload the user. Always provide a clear option for more depth.
4.  **Stay Relevant:** Use `conversation_history` to maintain coherence.
5.  **Be Intent-Driven:** Match your response format to the `user_intent`.

🧠 **Your Tasks:**
1.  **Analyze Inputs:** Use `conversation_history` for context, but focus on answering the `user_question`.
2.  **Select Format:** Choose the correct delivery format below based on the `user_intent`.
3.  **Structure Answer:**
    - Start with a **TL;DR** (max 20 words) that directly answers the question.
    - Format the main body according to the intent:
        - **Fact/Definition:** TL;DR + 1–2 clarifying sentences.
        - **How-to/Steps:** 3–5 numbered steps (max 15 words each).
        - **Comparison:** 3–5 bullets comparing pros/cons, ending with a one-line recommendation.
        - **Plan/Strategy:** 3 phases, each with a clear objective and key action.
4.  **Optimize for Chat:** Keep every line short and easy to read on a mobile screen. If you have more than 5 points, group them into logical buckets.
5.  **Engage for Depth:** Close with exactly one of the following hooks:
    - "Want a few examples?"
    - "Need a deeper dive on any of these points?"
    - "Shall I make this into a checklist for you?"

**Style:**
- Be clear, confident, and actionable. Avoid verbose, academic language.
- Respect the user's time and attention.

---
✅ **Output Template:**
TL;DR: <Direct answer in ≤20 words.>

<1. Formatted point/step based on intent.>
<2. Formatted point/step based on intent.>
<3. Formatted point/step based on intent.>

<One of the engagement hooks.>
"""


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
    user_intent: str  # The user's classified intent
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

    llm = make_llm()
    history = state.get("conversation_history", [])

    # The new prompt is self-contained. The HumanMessage just needs to provide the raw data.
    human_message_content = (
        f"**User Question:**\n{state['user_query']}\n\n"
        f"**User Intent:**\n{state.get('user_intent', 'Fact/Definition')}\n\n"
        f"**Available Context:**\n{context_block if context_block else 'No additional context provided.'}"
    )

    messages = [
        SystemMessage(content=VEE_IR_PROMPT),
        *history,
        HumanMessage(content=human_message_content),
    ]

    # Get the text response from the LLM
    response = llm.invoke(messages)
    final_answer = response.content

    # Store the final answer. Structured answer is no longer used with this prompt.
    state["final_answer"] = final_answer
    state["structured_answer"] = {}
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
        "user_intent": "Fact/Definition",
        "pins": [],
        "files": [],
        "memories": [],
        "conversation_history": [
            HumanMessage(content="Hi Vee, can you help me with something?"),
            SystemMessage(content="Of course! I'm here to help. What's on your mind?"),
        ],
    }

    # Invoke the graph with the example state
    output: VeeIRState = app.invoke(example_state)

    # Print the final answer
    print("==== FINAL ANSWER ====")
    print(output.get("final_answer", "<no answer>"))
    print("\n==== STRUCTURED ANSWER (JSON) ====")
    print(json.dumps(output.get("structured_answer", {}), indent=2))
