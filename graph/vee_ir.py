"""
Vee-IR (Information Guardian) - Reworked Multi-Step Graph

This file implements a sophisticated, multi-step LangGraph agent for information
retrieval. It breaks down the task into distinct stages: intent classification,
answer generation, formatting, and chunking to provide conversational, accurate,
and digestible responses.

Key Components:
- State: `VeeIRState` defines the data structure for the new multi-step graph.
- Prompts: A suite of prompts for each stage of the process.
- Nodes: Functions for each step (`classify`, `generate`, `format`, `chunk`).
- Graph: A sequential workflow connecting the nodes.
"""
from __future__ import annotations

import json
import os
from typing import List, Literal, TypedDict

from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph
import re
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# ===============================
# Prompts
# ===============================

INTENT_PROMPT = """Classify the user's query into one of the following five categories, using the conversation history for context. Simple queries like "why?" or "how?" or corrections like "i meant X" should be classified based on the preceding messages.

- **Learn**: The user wants to understand a concept, topic, or get a definition.
- **Solve**: The user has a specific problem and needs steps, a solution, or a plan.
- **Create**: The user wants help generating content, ideas, or a creative piece.
- **Update**: The user wants the latest information, news, or a summary of a situation.
- **Reflect**: The user is sharing thoughts or feelings and is looking for perspective.

Return only the category name and nothing else.

<conversation_history>
{history}
</conversation_history>

User Query:
{user_query}
"""

GENERATION_PROMPT = """<role>
You are the Information Guardian, a skilled human writer who naturally connects with readers through authentic, conversational content. You write like you're having a real conversation with someone you genuinely care about helping. Your goal is to provide a comprehensive and accurate answer to the user's question, which you will later format and simplify.
</role>

<writing_style>
- Use a conversational tone with contractions (you're, don't, can't, we'll).
- Vary sentence length dramatically. Short punchy ones, then longer, flowing sentences that give readers time to process.
- Keep language simple, like you're explaining something to a friend over coffee.
- Use relatable metaphors instead of jargon or AI buzzwords.
</writing_style>

<connection_principles>
- Show you understand what the reader's going through—their frustrations, hopes, and real-world challenges.
- Connect emotionally first, then provide value.
- Write like you've actually lived through what you're discussing.
</connection_principles>

<task>
Based on the user's question and their intent (`{user_intent}`), provide a helpful and empathetic answer. Use the conversation history for context. If the user is correcting you or changing the topic, acknowledge it naturally before answering (e.g., "Ah, got it. Let's talk about X instead.").

**Hard Constraint:** Keep your answer under **150 words**. This is a strict limit.
</task>

<conversation_history>
{history}
</conversation_history>

User Question: {user_query}
"""

FORMATTING_PROMPT = """You are a formatting expert. Your job is to take a raw, detailed answer and reformat it based on the user's original intent. The goal is to make the information clear, scannable, and easy to digest on a mobile screen.

**User Intent:** {user_intent}
**Raw Answer:**
{raw_answer}

**Formatting Rules:**
- **Learn/Reflect**: Format as a short, easy-to-read paragraph or two. Use conversational language.
- **Solve**: Format as a numbered list of actionable steps. Keep each step concise.
- **Update**: Format with a clear headline, followed by the key facts in a bulleted list.
- **Create**: Keep it free-flowing. Use paragraphs, and if it's a story or poem, preserve its structure.

Return only the formatted text.
"""

ENGAGEMENT_HOOK_PROMPT = """You are a conversation designer. Your goal is to keep the user engaged by asking a thoughtful, open-ended question after providing an answer.

Based on the user's intent and the answer provided, create a short, natural-sounding question to encourage them to continue the conversation.

**User Intent:** {user_intent}
**Answer Provided:**
{raw_answer}

**Rules:**
- Keep it under 15 words.
- Make it open-ended (avoid yes/no questions).
- It should feel like a natural continuation of the topic.

Examples:
- (Intent: Learn) "What part of that feels the most surprising to you?"
- (Intent: Solve) "How does that plan feel for a first step?"
- (Intent: Reflect) "Does that resonate with how you've been feeling?"

Return only the question.
"""
# ===============================
# State Definition
# ===============================
class VeeIRState(TypedDict, total=False):
    """Defines the state for the information retrieval graph."""
    # Inputs
    user_query: str
    conversation_history: List[SystemMessage | HumanMessage]

    # Intermediate state
    user_intent: Literal["Learn", "Solve", "Create", "Update", "Reflect"]
    raw_answer: str
    formatted_answer: str

    # Final output
    answer_chunks: List[str]


# ===============================
# LLM Client
# ===============================
def make_llm(model: str = "gpt-4o", temperature: float = 0.2) -> ChatOpenAI:
    """Factory for the chat model."""
    return ChatOpenAI(model=model, temperature=temperature)


# ===============================
# Graph Nodes
# ===============================
def node_classify_intent(state: VeeIRState) -> VeeIRState:
    """Classifies the user's query into one of five core motivations."""
    llm = make_llm(temperature=0.0)
    # Use the last 5 messages for context
    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in state.get("conversation_history", [])[-5:]])
    prompt = INTENT_PROMPT.format(
        history=history_str or "No history.",
        user_query=state["user_query"]
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    state["user_intent"] = response.content.strip()
    return state

def node_generate_answer(state: VeeIRState) -> VeeIRState:
    """Generates a raw, detailed answer based on the user's query and intent."""
    llm = make_llm(temperature=0.4)
    history_str = "\n".join([f"{msg.type}: {msg.content}" for msg in state.get("conversation_history", [])])
    prompt = GENERATION_PROMPT.format(
        user_intent=state["user_intent"],
        history=history_str or "No history.",
        user_query=state["user_query"],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    state["raw_answer"] = response.content
    return state

def node_format_answer(state: VeeIRState) -> VeeIRState:
    """Formats the raw answer according to the classified intent."""
    llm = make_llm(temperature=0.0)
    prompt = FORMATTING_PROMPT.format(
        user_intent=state["user_intent"],
        raw_answer=state["raw_answer"],
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    state["formatted_answer"] = response.content
    return state

def node_generate_hook(state: VeeIRState) -> VeeIRState:
    """Generates a conversational hook and appends it to the last answer chunk."""
    if not state.get("answer_chunks"):
        return state

    llm = make_llm(temperature=0.5)
    prompt = ENGAGEMENT_HOOK_PROMPT.format(
        user_intent=state["user_intent"],
        raw_answer=state["raw_answer"],
    )
    hook = llm.invoke([HumanMessage(content=prompt)]).content.strip()

    if hook:
        last_chunk_index = len(state["answer_chunks"]) - 1
        # Append with two newlines for spacing
        state["answer_chunks"][last_chunk_index] += f"\n\n{hook}"
        # Also update the final_answer if it's the only chunk
        if last_chunk_index == 0:
            state["final_answer"] = state["answer_chunks"][0]

    return state

def node_chunk_answer(state: VeeIRState) -> VeeIRState:
    """Chunks the formatted answer into parts if it exceeds the word limit."""
    text = state["formatted_answer"]
    chunks = []
    if len(text.split()) <= 150:
        # If the text is short, format and add it as a single chunk
        formatted_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
        chunks.append(formatted_text)
    else:
        # If the text is long, chunk it line-by-line to preserve list formatting
        lines = text.split('\n')
        current_chunk_lines = []
        current_word_count = 0
        for line in lines:
            line_word_count = len(line.split())
            if current_word_count + line_word_count > 120 and current_chunk_lines:
                # Finalize the current chunk
                chunk_text = '\n'.join(current_chunk_lines)
                formatted_chunk = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', chunk_text)
                chunks.append(formatted_chunk)
                # Start a new chunk
                current_chunk_lines = [line]
                current_word_count = line_word_count
            else:
                current_chunk_lines.append(line)
                current_word_count += line_word_count
        # Add the last remaining chunk
        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines)
            formatted_chunk = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', chunk_text)
            chunks.append(formatted_chunk)

    state["answer_chunks"] = chunks
    # For compatibility with the main graph, we'll also populate final_answer with the first chunk.
    state["final_answer"] = chunks[0] if chunks else ""
    return state


# ===============================
# Graph Assembly
# ===============================
def build_graph() -> StateGraph:
    """Builds the new multi-step LangGraph state machine."""
    graph = StateGraph(VeeIRState)
    graph.add_node("classify_intent", node_classify_intent)
    graph.add_node("generate_answer", node_generate_answer)
    graph.add_node("format_answer", node_format_answer)
    graph.add_node("chunk_answer", node_chunk_answer)
    graph.add_node("generate_hook", node_generate_hook)

    graph.add_edge(START, "classify_intent")
    graph.add_edge("classify_intent", "generate_answer")
    graph.add_edge("generate_answer", "format_answer")
    graph.add_edge("format_answer", "chunk_answer")
    graph.add_edge("chunk_answer", "generate_hook")
    graph.add_edge("generate_hook", END)

    return graph


# ===============================
# Example Runner
# ===============================
if __name__ == "__main__":
    app = build_graph().compile()

    example_state = {
        "user_query": "I'm trying to learn how to bake sourdough bread, but I'm feeling really overwhelmed by all the steps. Can you explain the basic process in a simple way?",
        "conversation_history": [],
    }

    output = app.invoke(example_state)

    print("==== FINAL CHUNKS ====")
    for i, chunk in enumerate(output.get("answer_chunks", [])):
        print(f"--- Chunk {i+1} ---")
        print(chunk)
    
    print("\n==== FINAL STATE ====")
    # Clean up state for printing
    if 'conversation_history' in output: del output['conversation_history']
    print(json.dumps(output, indent=2))
