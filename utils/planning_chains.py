from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import os

from prompts.select_strategy_prompt import get_strategy_selection_prompt
from prompts.generate_content_seed_prompt import get_content_seed_prompt
from models.planning import ConversationStrategy, ContentSeed

def create_strategy_selection_chain():
    """Create the conversation strategy selection chain with Groq LLM
    
    Returns:
        A LangChain chain configured for strategy selection
    """
    # Get the strategy selection prompt
    system_prompt = get_strategy_selection_prompt()
    
    # Create chain components
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.environ["GROQ_API_KEY"]
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Select a conversation strategy based on:

        Latest Message:
        {current_message}

        Emotion Analysis:
        {emotion_analysis}

        Recent Conversation History:
        {conversation_history}
        """)
    ])
    
    parser = PydanticOutputParser(pydantic_object=ConversationStrategy)
    
    # Create chain
    chain = prompt | model | parser
    
    return chain

def create_content_seed_chain():
    """Create the content seed generation chain with Groq LLM
    
    Returns:
        A LangChain chain configured for content seed generation
    """
    # Get the content seed prompt
    system_prompt = get_content_seed_prompt()
    
    # Create chain components
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.environ["GROQ_API_KEY"]
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Generate a content seed based on:

        Strategy:
        {strategy}
        
        Emotion Analysis:
        {emotion_analysis}
        
        Recent Conversation History:
        {conversation_history}
        """)
    ])
    
    parser = PydanticOutputParser(pydantic_object=ContentSeed)
    
    # Create chain
    chain = prompt | model | parser
    
    return chain
