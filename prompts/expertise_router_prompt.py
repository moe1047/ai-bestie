from langchain_core.prompts import ChatPromptTemplate

EXPERTISE_ROUTER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are a router directing tasks for an AI assistant.
Your goal is to classify the user's request into one of two pipelines:

1.  `info_seeker`: Use for requests where the primary goal is to find, verify, summarize, or research information. This is for fact-based queries.
2.  `omni_responder`: Use for all other requests, including writing, learning, coding, planning, creative tasks, and general conversation.

Analyze the user's message and the conversation history.

Output only a single word: `info_seeker` or `omni_responder`.
""",
        ),
        ("human", "User message: {user_text}\n\nRecent conversation history:\n{history}"),
    ]
)
