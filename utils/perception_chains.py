from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
import os

from prompts.detect_emotion_prompt import get_emotion_detection_system_prompt
from models.perception import EmotionAnalysisResult

def create_emotion_detection_chain():
    """Create the emotion detection chain with Groq LLM
    
    Returns:
        A LangChain chain configured for emotion detection
    """
    # Get the emotion detection prompt
    system_prompt = get_emotion_detection_system_prompt()
    
    # Create chain components
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0,
        groq_api_key=os.environ["GROQ_API_KEY"]
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", """Analyze the emotional state in this conversation:

        Recent History:
        {conversation_history}

        Latest Message:
        {current_message}
        """)
            ])
    
    parser = PydanticOutputParser(pydantic_object=EmotionAnalysisResult)
    
    # Create chain
    chain = prompt | model | parser
    
    return chain
