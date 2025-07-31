from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string
from dotenv import load_dotenv
from utils.perception_chains import create_emotion_detection_chain
from utils.planning_chains import create_strategy_selection_chain, create_content_seed_chain
from utils.acting_chains import create_response_modulation_chain
load_dotenv()

def get_sample_message():
    """Returns the current message for testing."""
    return "I feel so overwhelmed... my anxiety is through the roof. trying to smile through meetings but inside I'm just... drowning 💔"

def get_sample_conversation():
    """Returns a sample conversation for testing."""
    return [
        AIMessage(content="hey, I've noticed you've been a bit quiet lately... how are you really doing? 🫂"),
        HumanMessage(content="idk... work has been intense. trying to keep it together but some days are just... a lot 😮‍💨"),
        AIMessage(content="I hear you... and it's okay to not have it all figured out. would you like to talk about what's making things feel heavy, or would you prefer a gentle distraction?"),
        HumanMessage(content="maybe just distraction for now. not ready to unpack all of that..."),
        AIMessage(content="of course 💛 let's take it easy. sometimes just being present is enough. want to hear about this adorable cat video I came across?")  
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
    try:
        print("\nAnalyzing conversation...\n")
        
        # Test individual components
        print("[DEBUG] Getting sample conversation...")
        messages = get_sample_conversation()
        current_message = get_sample_message()
        
        print("\n[DEBUG] Testing emotion analysis:")
        print(f"[DEBUG] Messages: {[m.content for m in messages]}")
        print(f"[DEBUG] Current message: {current_message}")
        emotion_result = analyze_emotion(messages, current_message)
        print("[DEBUG] Emotion analysis complete")
        print_emotion_analysis(emotion_result)
        
        print("\n[DEBUG] Testing strategy selection:")
        recent_history = get_buffer_string(messages[-3:])
        print(f"[DEBUG] Recent history: {recent_history}")
        print(f"[DEBUG] Emotion result: {emotion_result.model_dump()}")
        strategy_result = select_strategy(current_message, emotion_result, recent_history)
        print("[DEBUG] Strategy selection complete")
        print_strategy_selection(strategy_result)
        
        print("\n[DEBUG] Testing content seed generation:")
        content_seed = generate_content_seed(strategy_result, emotion_result, recent_history)
        print("[DEBUG] Content seed generation complete")
        print_content_seed(content_seed)
        
        print("\n[DEBUG] Testing response modulation:")
        modulated = modulate_response(content_seed, strategy_result, emotion_result, recent_history)
        print("[DEBUG] Response modulation complete")
        print_modulated_response(modulated)
        
        print("\n[DEBUG] Testing full pipeline:")
        results = analyze_and_plan_conversation()
        print("[DEBUG] Full pipeline complete")
        print("\nEmotion Analysis:")
        print_emotion_analysis(results["emotion_analysis"])
        print("\nStrategy Selection:")
        print_strategy_selection(results["conversation_strategy"])
        print("\nContent Seed:")
        print_content_seed(results["content_seed"])
        print("\nModulated Response:")
        print_modulated_response(results["modulated_response"])
            
    except Exception as e:
        import traceback
        print(f"\n[ERROR] An error occurred: {str(e)}")
        print("[ERROR] Traceback:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
