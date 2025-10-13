from llms.llm_factory import get_groq_llm
from utils.file_io import load_prompt
from langchain_core.prompts import ChatPromptTemplate

def summarize_session_narrative(conversation_history: str, user_name: str) -> str:
    """
    Generates a narrative summary of a conversation session using an LLM.
    """
    print("\n--- GENERATING SESSION SUMMARY ---")
    
    # 1. Get LLM - Using a smaller, faster model for summarization is efficient.
    llm = get_groq_llm(model_name="llama3-8b-8192", temperature=0.5)
    
    # 2. Load Prompt
    prompt_template_str = load_prompt("memory/summarizer_prompt.md")
    
    # 3. Create Prompt Template
    prompt_template = ChatPromptTemplate.from_template(prompt_template_str)
    
    # 4. Create Chain
    summarizer_chain = prompt_template | llm
    
    # 5. Invoke Chain
    response = summarizer_chain.invoke({
        "user_name": user_name,
        "conversation_history": conversation_history
    })
    
    summary = response.content.strip()
    print(f"Generated summary: '{summary[:100]}...'"    )
    
    return summary
