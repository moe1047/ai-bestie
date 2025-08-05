from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string
from dotenv import load_dotenv
from graph.build_graph import build_graph, get_default_state
from utils.perception_chains import create_emotion_detection_chain
from utils.planning_chains import create_strategy_selection_chain, create_content_seed_chain
from utils.acting_chains import create_response_modulation_chain
load_dotenv()

def get_sample_message():
    """Returns the current message for testing."""
    return "hi there"

def get_sample_conversation():
    """Returns a sample conversation for testing."""
    return [
    ]

def analyze_emotion(messages, current_message):
    """Analyze emotions in a conversation.
    
    Args:
        messages: List of conversation messages
        current_message: The latest message to analyze
        
    Returns:
        EmotionAnalysisResult object
    """
    chain = create_emotion_detection_chain()
    
    # Get last 3 messages from history
    recent_messages = messages[-3:] if len(messages) >= 3 else messages
    conversation_history = get_buffer_string(recent_messages)
    
    # Run emotion analysis
    return chain.invoke({
        "conversation_history": conversation_history,
        "current_message": current_message
    })

def select_strategy(current_message, emotion_result, conversation_history):
    """Select conversation strategy based on emotion analysis.
    
    Args:
        current_message: The latest message
        emotion_result: Result from emotion analysis
        conversation_history: Recent conversation history
        
    Returns:
        ConversationStrategy object
    """
    chain = create_strategy_selection_chain()
    
    return chain.invoke({
        "current_message": current_message,
        "emotion_analysis": emotion_result.model_dump(),
        "conversation_history": conversation_history
    })

def analyze_and_plan_conversation(messages=None, current_message=None):
    """Run full conversation pipeline including emotion analysis, planning, and response modulation.
    
    Args:
        messages: Optional list of conversation messages (uses sample if None)
        current_message: Optional current message (uses sample if None)
        
    Returns:
        Dict containing all pipeline results
    """
    # Use sample data if none provided
    if messages is None:
        messages = get_sample_conversation()
    if current_message is None:
        current_message = get_sample_message()
    
    # Get conversation history
    recent_messages = messages[-3:] if len(messages) >= 3 else messages
    recent_history = get_buffer_string(recent_messages)
    
    # Run emotion analysis
    emotion_result = analyze_emotion(messages, current_message)
    
    # Select conversation strategy
    strategy_result = select_strategy(current_message, emotion_result, recent_history)
    
    # Generate content seed
    content_seed = generate_content_seed(strategy_result, emotion_result, recent_history)
    
    # Modulate final response
    modulated_response = modulate_response(content_seed, strategy_result, emotion_result, recent_history)
    
    return {
        "emotion_analysis": emotion_result,
        "conversation_strategy": strategy_result,
        "content_seed": content_seed,
        "modulated_response": modulated_response
    }

def print_emotion_analysis(result):
    """Print emotion analysis results in a formatted way."""
    print("\nEmotion Analysis:")
    print(f"Emotion: {result.emotion}")
    print(f"Tone: {result.tone}")
    if result.notes:
        print(f"Notes: {result.notes}")

def print_strategy_selection(strategy):
    """Print strategy selection results in a readable format."""
    print("Selected Strategy:", strategy.strategy)
    print("Rationale:", strategy.rationale)

def generate_content_seed(strategy, emotion_result, conversation_history):
    """Generate a content seed based on strategy and emotion analysis.
    
    Args:
        strategy: ConversationStrategy object
        emotion_result: EmotionAnalysisResult object
        conversation_history: String of recent conversation history
        
    Returns:
        ContentSeed object with seed and optional tag
    """
    print("\n[DEBUG] Generating content seed...")
    print(f"[DEBUG] Strategy: {strategy.model_dump()}")
    print(f"[DEBUG] Emotion Analysis: {emotion_result.model_dump()}")
    print(f"[DEBUG] Conversation History: {conversation_history}")
    
    chain = create_content_seed_chain()
    print("[DEBUG] Chain created, invoking...")
    
    result = chain.invoke({
        "strategy": strategy.model_dump(),
        "emotion_analysis": emotion_result.model_dump(),
        "conversation_history": conversation_history
    })
    
    print(f"[DEBUG] Content seed generated: {result.model_dump()}")
    return result

def print_content_seed(seed):
    """Print content seed results in a readable format."""
    print("Content Seed:", seed.seed)
    if seed.tag:
        print("Tag:", seed.tag)

def modulate_response(content_seed, strategy, emotion_result, conversation_history):
    """Modulate the response based on content seed and context.
    
    Args:
        content_seed: ContentSeed object
        strategy: ConversationStrategy object
        emotion_result: EmotionAnalysisResult object
        conversation_history: String of recent conversation history
        
    Returns:
        str: The modulated response message
    """
    print("\n[DEBUG] Modulating response...")
    print(f"[DEBUG] Content Seed: {content_seed.seed}")
    print(f"[DEBUG] Strategy: {strategy.strategy}")
    print(f"[DEBUG] Emotion: {emotion_result.emotion}")
    print(f"[DEBUG] Conversation History: {conversation_history}")
    
    chain = create_response_modulation_chain()
    print("[DEBUG] Chain created, invoking...")
    
    result = chain.invoke({
        "content_seed": content_seed.seed,
        "strategy": strategy.strategy,
        "emotion_analysis": f"Emotion: {emotion_result.emotion}, Tone: {emotion_result.tone}",
        "tag": content_seed.tag or "none",
        "conversation_history": conversation_history
    })
    
    print(f"[DEBUG] Response modulated: {result}")
    return result

def print_modulated_response(response):
    """Print modulated response in a readable format."""
    print("\nModulated Response:")
    print(response)

def main():
    """Main function for testing the Vee conversation graph."""
    try:
        print("[DEBUG] Building conversation graph...")
        graph = build_graph()
        
        print("\n[DEBUG] Creating initial state...")
        state = get_default_state()
        print(f"[DEBUG] Initial message: {state['messages'][-1].content}")
        
        print("[DEBUG] Running conversation graph...")
        result = graph.invoke(
            state,
            config={"configurable": {"thread_id": "test_session"}}
        )
        
        print("\n[DEBUG] Final state:")
        print("\nPerception:")
        print(f"Emotion: {result['perception']['current']['emotion']}")
        print(f"Tone: {result['perception']['current']['tone']}")
        print(f"Notes: {result['perception']['current']['notes']}")
        
        print("\nPlanning:")
        print(f"Strategy: {result['planning']['current']['strategy']}")
        print(f"Rationale: {result['planning']['current']['rationale']}")
        print(f"Content Seed: {result['planning']['current']['content_seed']}")
        
        print("\nConversation:")
        for msg in result['messages']:
            prefix = "AI: " if isinstance(msg, AIMessage) else "Human: "
            print(f"{prefix}{msg.content}")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        print("[ERROR] Traceback:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
