# Vee: The Dual-Mode AI Companion 🧠❤️

Vee is a next-generation AI companion built on a sophisticated, dual-mode architecture. It seamlessly transitions between a deeply empathetic **Bestie** and a hyper-competent **Assistant**, providing exactly the right kind of support, whether you need a friend to listen or an expert to solve a problem.

Powered by LangGraph, Vee uses a dynamic, state-aware workflow to deliver conversations that are not just intelligent, but genuinely attuned to you.

## Core Features

Vee is more than just a chatbot; it's a versatile companion designed to handle a wide range of needs.

- **Dual-Mode Personality**:
    - **Bestie Mode**: Offers empathetic, supportive, and non-judgmental conversation when you need a friend.
    - **Assistant Mode**: Provides clear, factual, and well-researched answers to your questions.

- **Advanced Information Retrieval**:
    - When in Assistant mode, Vee uses a sophisticated, multi-agent system (`Info-Seeker`) to research complex topics.
    - It can break down your query, perform targeted web searches, synthesize information, and provide a structured, easy-to-understand answer.

- **Context-Aware Conversation**:
    - Vee remembers the last few turns of your conversation, ensuring its responses are relevant and follow the flow of dialogue.
    - It analyzes your emotional state and conversational intent (`sense_text_node`) to tailor its responses appropriately.

- **Safety First**:
    - Every user message is analyzed by a `safety_triage_node` to assess risk and ensure conversations remain safe and constructive.

- **Dynamic UI**:
    - The system can present interactive buttons, allowing for clearer user feedback and control over the conversation flow.

## Technical Architecture

Vee's intelligence is orchestrated by a modular LangGraph workflow that ensures the right tools are used at the right time.

```
[User Input] -> Ingest -> Safety Check -> Perception (Sense Emotion)
              |
              +--> Mode Decider --+--> [Bestie Mode] -> Planner (Vee's Heart & Mind) -> Bestie Drafter (Vee's Voice) -> Review -> [Output]
              |                   |
              |                   +--> [Assistant Mode] -> Planner (Assistant Logic) -> Expertise Router --+--> Omni-Responder -> Assistant Drafter -> Review -> [Output]
              |                                                                                        |
              |                                                                                        +--> Info-Seeker (Multi-Agent) -> Assistant Drafter -> Review -> [Output]
              |
              +--------------------------------------------------------------------------------------------> [Final Output]
```

### Key Components

- **Mode-Aware Planner**: A single, unified planner node (`plan_next_move`) that dynamically selects the correct LLM prompt and logic based on the active mode (`bestie` or `assistant`).
- **Stateful Routing**: The graph uses conditional edges (`mode_decider`, `post_planning_router`) that read the `mode` from the `VeeState` to direct the workflow, eliminating redundant nodes and creating a clean, explicit data flow.
- **Info-Seeker Subgraph**: A self-contained multi-agent system for advanced research, demonstrating a powerful graph-within-a-graph architecture.
- **Persona Drafters**: Separate `bestie_drafter` and `assistant_drafter` nodes ensure that the final response has the perfect tone and personality for the chosen mode.

## Getting Started with Docker

This project is fully containerized with Docker, making setup and deployment straightforward for both local development and production.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Environment Variables

Before you begin, create a `.env` file in the root of the project and add your API keys and tokens:

```
GROQ_API_KEY="your_groq_api_key_here"
TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
WEBHOOK_URL="your_ngrok_or_vps_url/webhook" # e.g., https://heyyvee.com/webhook
```

### Local Development

For local development, the application uses an Nginx configuration that listens on `http://localhost`.

1.  **Build and run the containers:**
    ```bash
    docker-compose up --build
    ```
    This will start the application. By default, Nginx is mapped to port 90 to avoid conflicts on local machines (`http://localhost:90`).

2.  **Set the Telegram Webhook (if using Telegram):**
    You'll need a tool like [ngrok](https://ngrok.com/) to expose your local server to the internet. Once you have your ngrok URL, set the webhook:
    ```bash
    curl -F "url=https://your-ngrok-url.io/webhook" https://api.telegram.org/bot<YOUR_TELEGRAM_BOT_TOKEN>/setWebhook
    ```
    Remember to update the `WEBHOOK_URL` in your `.env` file with the ngrok URL.

### Production Deployment

The production setup uses Nginx with SSL certificates from Let's Encrypt, managed by Certbot.

1.  **Server Setup**:
    - Get a VPS and install Docker and Docker Compose.
    - Point your domain(s) (e.g., `heyyvee.com`, `perceive.heyyvee.com`) to your VPS's public IP address via an `A` record.

2.  **Run the Application**:
    On your VPS, run the following command to start the application using the production Nginx configuration:
    ```bash
    NGINX_CONF=prod.conf docker-compose up -d --build
    ```

3.  **Obtain SSL Certificate**:
    With the containers running, execute the Certbot command to get your SSL certificate. This command requests a certificate for multiple domains.
    ```bash
    docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot --email your-email@example.com --agree-tos --no-eff-email -d heyyvee.com -d perceive.heyyvee.com
    ```

4.  **Restart Nginx**:
    After the certificate is successfully created, restart Nginx to apply the new SSL configuration:
    ```bash
    docker-compose restart nginx
    ```
    Your application is now live and secure at `https://heyyvee.com`.

## Dependencies

- Python 3.8+
- LangChain & LangGraph
- Groq for LLM inference
- Pydantic for data modeling
- python-telegram-bot for the Telegram UI
## License

MIT License - Feel free to use and modify as needed.
