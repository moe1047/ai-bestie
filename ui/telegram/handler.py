import asyncio
import logging
import json
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from langchain_core.messages import AIMessage, HumanMessage
from graph.build_graph import build_graph
from ui.telegram.client import TelegramClient
from memory import crud, schemas

logger = logging.getLogger(__name__)


async def keep_typing(telegram_client, chat_id, interval=4):
    try:
        while True:
            await telegram_client.send_chat_action(chat_id, "typing")
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass


class TelegramHandler:
    def __init__(self, telegram_client: TelegramClient, db_write_queue):
        self.telegram_client = telegram_client
        # Build the graph without a checkpointer for stateless operation
        self.graph = build_graph(checkpointer=None)
        self.session_cache = {}
        self.db_write_queue = db_write_queue


    async def _stream_response(self, chat_id, input_data):
        """Run the graph to completion, send the final response, and update the cache."""
        config = {"configurable": {"thread_id": str(chat_id)}}
        final_state = None

        # 1. Stream the graph execution
        async for chunk in self.graph.astream(input_data, config, stream_mode="values"):
            final_state = chunk

        # 2. After the stream is complete, extract the final response
        if final_state and final_state.get("messages"):
            final_draft = final_state["messages"][-1].content
            if final_draft:
                # Send the single, complete message
                await self.telegram_client.send_message(
                    chat_id, final_draft, parse_mode="MarkdownV2"
                )

            # 3. Update the session cache with the new message history
            if chat_id in self.session_cache:
                self.session_cache[chat_id]["messages"] = final_state.get("messages", [])
                logger.info(f"Updated message history in cache for chat {chat_id}.")


    async def handle_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        user_message = update.message.text
        chat_id = update.message.chat_id

        if user_message == "/start":
            welcome_message = "Hey! 👋 I'm Vee, your bestie. I'm here to support you emotionally and give you any information you want about anything in this world, all in the easiest way possible. 😊"
            await self.telegram_client.send_message(chat_id, welcome_message)
            # Clear any existing session cache for a clean start
            if chat_id in self.session_cache:
                del self.session_cache[chat_id]
            return

        typing_task = asyncio.create_task(keep_typing(self.telegram_client, chat_id))
        try:
            # 1. Get User, Session, and Message History from Cache or DB
            if chat_id in self.session_cache:
                cached_data = self.session_cache[chat_id]
                cached_data = self.session_cache[chat_id]
                user = cached_data["user"]
                session = cached_data["session"]
                # Always fetch a fresh, limited message history from the DB
                messages = crud.get_recent_messages(session.id)
                logger.info(f"Loaded user and session from cache. Fetched {len(messages)} recent messages from DB for chat {chat_id}.")
            else:
                user = crud.get_or_create_user(chat_id, name="User")
                session = crud.get_active_session(user.id)
                if not session:
                    session = crud.create_session(user.id)
                    messages = [] # No previous messages for a new session
                    logger.info(f"Created new session {session.id} for user {user.id}.")
                else:
                    # Existing session, load its history
                    messages = crud.get_recent_messages(session.id)
                    logger.info(f"Loaded {len(messages)} messages from DB for existing session {session.id}.")

                # Store everything in the cache
                self.session_cache[chat_id] = {"user": user, "session": session, "messages": messages}
                logger.info(f"Cached user, session, and message history for chat {chat_id}.")

            # 2. Prepare the input state for the graph
            input_data = {
                "user": user,
                "session": session,
                "last_user_text": user_message,
                "messages": messages + [HumanMessage(content=user_message)],
                "db_write_queue": self.db_write_queue,
            }
            logger.info(f"[State Debug] Final input state for chat {chat_id}: {json.dumps(input_data, indent=2, default=str)}")

            # 3. Stream Response
            await self._stream_response(chat_id, input_data)
            

        finally:
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass
