import asyncio
import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import AIMessage, HumanMessage
from graph.build_graph import build_graph
from ui.telegram.client import TelegramClient

logger = logging.getLogger(__name__)


async def keep_typing(telegram_client, chat_id, interval=4):
    try:
        while True:
            await telegram_client.send_chat_action(chat_id, "typing")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass


class TelegramHandler:
    def __init__(self, telegram_client: TelegramClient, checkpointer):
        self.telegram_client = telegram_client
        self.graph = build_graph(checkpointer)

    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None:
            return

        user_message = update.message.text
        chat_id = update.message.chat_id

        if user_message == "/start":
            welcome_message = "Hey! 👋 I'm Vee, your bestie. I'm here to support you emotionally and give you any information you want about anything in this world, all in the easiest way possible. 😊"
            await self.telegram_client.send_message(chat_id, welcome_message)
            return

        # Start typing indicator
        typing_task = asyncio.create_task(keep_typing(self.telegram_client, chat_id))

        try:
            logger.info(f"[State Debug] Retrieving state for chat {chat_id}...")
            current_state = await self.graph.aget_state(config={"configurable": {"thread_id": str(chat_id)}})
            
            # Log current state
            if current_state:
                logger.info(f"[State Debug] Found existing state: {current_state.values}")
            else:
                logger.info(f"[State Debug] No existing state found, initializing new state")
            
            # Get the current state's values, or an empty dict if no state exists
            input_data = current_state.values if current_state and hasattr(current_state, 'values') else {}

            # If it's a new conversation, initialize the required structure
            if not input_data:
                logger.info(f"[State Debug] Initializing new state for chat {chat_id}")
                input_data = {
                    "messages": [],
                    "sensing": {"current": {}, "history": []},
                    "planning": {"current": {}, "history": []},
                    "acting": {},
                    "session": {
                        "start_time": datetime.now().isoformat(),
                        "last_update": datetime.now().isoformat(),
                        "context": {}
                    },
                    "user": {
                        "name": None,
                        "phone_number": None,
                        "chat_id": str(chat_id)
                    }
                }
            else:
                logger.info(f"[State Debug] Loaded existing state for chat {chat_id}: {input_data}")

            # Append the new user message to the history
            messages = input_data.get("messages", [])
            messages.append(HumanMessage(content=user_message))
            input_data["messages"] = messages
            logger.info(f"[State Debug] Final input state before streaming for chat {chat_id}: {json.dumps(input_data, indent=2, default=str)}")

            # Stream through LangGraph
            async for chunk in self.graph.astream(
                input_data,
                config={"configurable": {"thread_id": str(chat_id)}},
                stream_mode="messages",
            ):
                pass

        finally:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

        # Get final response from persisted state
        output_state = await self.graph.aget_state(config={"configurable": {"thread_id": str(chat_id)}})
        final_draft = output_state.values.get("draft")

        if final_draft:
            if isinstance(final_draft, list):
                for chunk in final_draft:
                    await self.telegram_client.send_message(chat_id, chunk, parse_mode="HTML")
            elif isinstance(final_draft, str):
                await self.telegram_client.send_message(chat_id, final_draft, parse_mode="HTML")
