import asyncio
import logging
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
            
            # Pass user's message directly to the graph as input
            input_data = {
                "messages": [],
                "sensing": {
                    "current": {
                        "emotion": None,
                        "tone": None,
                        "notes": None,
                        "timestamp": None
                    },
                    "history": []
                },
                "planning": {
                    "current": {
                        "strategy": None,
                        "rationale": None,
                        "content_seed": None,
                        "tag": None,
                        "timestamp": None
                    },
                    "history": []
                },
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
            
            # Add new message to existing messages
            # Update with existing state if available
            if current_state and hasattr(current_state, 'values'):
                logger.info(f"[State Debug] Merging with existing state values")
                try:
                    input_data.update(current_state.values)
                    logger.info(f"[State Debug] State merge successful")
                except Exception as e:
                    logger.error(f"[State Debug] Error merging state: {e}")
            
            # Append new message
            input_data["messages"].append(HumanMessage(content=user_message))
            print("input_data ========>",input_data)

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
                    await self.telegram_client.send_message(chat_id, chunk)
            elif isinstance(final_draft, str):
                await self.telegram_client.send_message(chat_id, final_draft)
