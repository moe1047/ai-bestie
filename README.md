# Vee - Your Emotionally Intelligent AI Companion 🫂

Vee is an advanced AI companion designed to provide empathetic, emotionally intelligent conversations. Using LangGraph for state management and a sophisticated pipeline of perception, planning, and response modulation, Vee creates genuine, supportive interactions that adapt to your emotional state.

## Core Features

- **Emotional Intelligence**: Detects and responds to subtle emotional cues, tone shifts, and underlying feelings
- **Adaptive Conversations**: Dynamically adjusts conversation strategies based on your emotional state
- **Natural Interactions**: Generates authentic, contextually appropriate responses with appropriate emotional depth
- **Safe Space**: Creates a judgment-free environment for sharing and processing emotions
- **Multi-Platform Support**: Available through Telegram bot interface
- **State Management**: Robust conversation state tracking with LangGraph

## Technical Architecture

The conversation pipeline consists of three main phases:

1. **Perception** 🔍
   - Emotion detection
   - Tone analysis
   - Context understanding
   - State tracking with LangGraph

2. **Planning** 🧠
   - Strategy selection
   - Content seed generation
   - Emotional safety checks
   - Conversation flow management

3. **Response Modulation** 💬
   - Message crafting
   - Tone adjustment
   - Emotional resonance
   - Platform-specific formatting

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up your environment variables in `.env`:
   ```bash
   GROQ_API_KEY=your_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token  # If using Telegram bot
   ```

## Usage

### Console Interface
Run the main script to test Vee's conversation capabilities:
```bash
python3 main.py
```

### Telegram Bot
Start the Telegram bot interface:
```bash
python3 run_telegram_bot.py
```

## Dependencies

- Python 3.8+
- LangChain
- LangGraph
- Groq LLM integration
- Pydantic
- python-dotenv
- python-telegram-bot

## License

MIT License - Feel free to use and modify as needed.
