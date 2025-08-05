"""Configuration for Telegram integration."""
import os
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class TelegramSettings(BaseSettings):
    """Settings for Telegram bot integration."""
    TELEGRAM_BOT_TOKEN: str
    WEBHOOK_URL: str
    
    model_config = ConfigDict(env_file='.env', extra='allow')
