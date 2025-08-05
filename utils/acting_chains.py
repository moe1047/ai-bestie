import os
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from prompts.modulate_response_prompt import get_response_modulation_prompt

def create_response_modulation_chain():
    """Create a chain for modulating responses in Vee's style.
    
    Returns:
        Chain that takes content seed, strategy, emotion analysis and returns a modulated message
    """
    # Get the response modulation prompt
    system_prompt = get_response_modulation_prompt()
    
    # Create chain components
    model = ChatGroq(
        model="moonshotai/kimi-k2-instruct",
        temperature=0.4,
        groq_api_key=os.environ["GROQ_API_KEY"]
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Here is the data to write the next response:

        Content Seed:
        {content_seed}
        
        Your friend's Emotion Analysis:
        {emotion_analysis}

        Recent Conversation History:
        {conversation_history}
        """)
    ])
    
    # Create chain that extracts just the message content
    chain = prompt | model | (lambda x: x.content)
    
    return chain
