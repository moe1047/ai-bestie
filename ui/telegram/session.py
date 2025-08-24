"""Session management for Telegram bot with in-memory fallback."""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class SessionManager:
    """Manages persistent session state for Telegram chats with in-memory fallback."""
    
    def __init__(self, redis_url: Optional[str] = None):
        """Initialize storage backend.
        
        Args:
            redis_url: Optional Redis URL. If None, uses in-memory storage.
        """
        self.redis_enabled = False
        self.memory_store = {}  # Fallback in-memory storage
        
        if redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(redis_url)
                self.redis_enabled = True
                logger.info("Using Redis for session storage")
            except ImportError:
                logger.warning("Redis not available, using in-memory storage")
        else:
            logger.info("Using in-memory session storage")
        
    def _get_key(self, chat_id: str) -> str:
        """Get Redis key for a chat session."""
        return f"telegram:session:{chat_id}"
        
    async def _serialize_messages(self, messages: list) -> list:
        """Serialize message objects to JSON-compatible format."""
        serialized = []
        for msg in messages:
            if isinstance(msg, (HumanMessage, AIMessage)):
                serialized.append({
                    "type": msg.__class__.__name__,
                    "content": msg.content
                })
        return serialized
        
    async def _deserialize_messages(self, messages: list) -> list:
        """Deserialize messages from JSON format back to message objects."""
        deserialized = []
        for msg in messages:
            if msg["type"] == "HumanMessage":
                deserialized.append(HumanMessage(content=msg["content"]))
            elif msg["type"] == "AIMessage":
                deserialized.append(AIMessage(content=msg["content"]))
        return deserialized
    
    async def get_session(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for a chat ID."""
        try:
            if self.redis_enabled:
                data = await self.redis.get(f"telegram:session:{chat_id}")
                if data:
                    return json.loads(data)
            else:
                # Use in-memory fallback
                return self.memory_store.get(chat_id)
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting session for chat {chat_id}: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting session for chat {chat_id}: {e}")
            return None
            
    async def save_session(self, chat_id: str, state: Dict[str, Any]) -> bool:
        """Save session data for a chat ID."""
        try:
            if self.redis_enabled:
                # Store in Redis with 24-hour expiry
                await self.redis.setex(
                    f"telegram:session:{chat_id}",
                    24 * 60 * 60,  # 24 hours in seconds
                    json.dumps(state)
                )
            else:
                # Store in memory
                self.memory_store[chat_id] = state
            return True
            
        except Exception as e:
            logger.error(f"Error saving session for chat {chat_id}: {e}")
            return False
            
    async def create_initial_state(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Create initial state for a new session."""
        now = datetime.now().isoformat()
        state = {
            "messages": [HumanMessage(content=text)],
            "session": {
                "start_time": now,
                "last_update": now,
                "context": {}
            },
            "user": {
                "name": None,
                "phone_number": None,
                "chat_id": str(chat_id)
            },
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
            "next_node": None,
            "checkpoint": now
        }
        
        # Ensure all access is dictionary-style
        return {str(k): v for k, v in state.items()}
