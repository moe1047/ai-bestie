"""Telegram API client for Vee AI companion."""
import aiohttp
import re
from typing import Optional, AsyncContextManager
from contextlib import asynccontextmanager

class TelegramClient:
    def __init__(self, token: str, base_url: Optional[str] = None):
        self.token = token
        self.base_url = base_url or "https://api.telegram.org"
        self._session: Optional[aiohttp.ClientSession] = None
        
    def _get_api_url(self, method: str) -> str:
        """Get full API URL for a given method."""
        return f"{self.base_url}/bot{self.token}/{method}"

    def _escape_markdown(self, text: str) -> str:
        """Escapes characters for Telegram's MarkdownV2 parser."""
        # Characters that have special meaning in MarkdownV2 and need to be escaped.
        escape_chars = r'[_*[]()~`>#+-=|{}.!]'
        # Use re.sub to find and escape these characters.
        # The pattern looks for any character in the escape_chars string.
        # The replacement adds a backslash before the matched character.
        return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
    
    @asynccontextmanager
    async def get_session(self) -> AsyncContextManager[aiohttp.ClientSession]:
        """Get or create an aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        try:
            yield self._session
        finally:
            if not self._session.closed:
                await self._session.close()
    
    async def get_me(self) -> dict:
        """Get information about the bot."""
        url = self._get_api_url("getMe")
        async with self.get_session() as session:
            async with session.get(url) as response:
                result = await response.json()
                if not result.get("ok"):
                    raise Exception(f"Failed to get bot info: {result}")
                return result.get("result", {})
    
    async def send_message(self, chat_id: int, text: str, parse_mode: Optional[str] = "MarkdownV2", request_contact: bool = False) -> dict:
        """Send a message to a chat with optional contact request button."""
        url = self._get_api_url("sendMessage")

        message_text = text
        if parse_mode == "MarkdownV2":
            message_text = self._escape_markdown(text)

        data = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": parse_mode
        }
        
        if request_contact:
            # Add a custom keyboard with a Share Contact button
            data["reply_markup"] = {
                "keyboard": [[
                    {
                        "text": "📱 Share Contact",
                        "request_contact": True
                    }
                ]],
                "resize_keyboard": True,
                "one_time_keyboard": True  # Keyboard disappears after use
            }
        
        async with self.get_session() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                if not result.get("ok"):
                    raise Exception(f"Failed to send message: {result}")
                return result
                
    async def send_chat_action(self, chat_id: int, action: str) -> dict:
        """Send a chat action to indicate bot's status (typing, uploading, etc).
        
        Args:
            chat_id: Telegram chat ID
            action: One of: typing, upload_photo, record_video, upload_video,
                   record_voice, upload_voice, upload_document, choose_sticker,
                   find_location, record_video_note, upload_video_note
        """
        url = self._get_api_url("sendChatAction")
        data = {
            "chat_id": chat_id,
            "action": action
        }
        
        async with self.get_session() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                if not result.get("ok"):
                    raise Exception(f"Failed to send chat action: {result}")
                return result
                
    async def set_webhook(self, webhook_url: str) -> dict:
        """Set the webhook URL for receiving updates."""
        url = self._get_api_url("setWebhook")
        data = {"url": webhook_url}
        
        async with self.get_session() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                if not result.get("ok"):
                    raise Exception(f"Failed to set webhook: {result}")
                return result
                
    async def delete_webhook(self) -> dict:
        """Remove the webhook integration."""
        url = self._get_api_url("deleteWebhook")
        
        async with self.get_session() as session:
            async with session.post(url) as response:
                result = await response.json()
                if not result.get("ok"):
                    raise Exception(f"Failed to delete webhook: {result}")
                return result
