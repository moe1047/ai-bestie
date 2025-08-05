"""FastAPI application for Telegram webhook handler for Vee AI companion."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update
from ui.telegram.client import TelegramClient
from ui.telegram.handler import TelegramHandler
from ui.telegram.config import TelegramSettings

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load settings
settings = TelegramSettings()

# Initialize Telegram client and handler
telegram_client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
telegram_handler = TelegramHandler(telegram_client)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    try:
        # Startup: verify bot and set webhook
        async with telegram_client.get_session() as session:
            me = await telegram_client.get_me()
            logger.info(f"Bot authorized as: {me.get('username')}")
        
        result = await telegram_client.set_webhook(settings.WEBHOOK_URL)
        if not result.get("ok"):
            raise Exception(f"Failed to set webhook: {result}")
            
        logger.info("Webhook set successfully")
        yield
        
        # Shutdown: clean up webhook
        await telegram_client.delete_webhook()
        logger.info("Webhook deleted successfully")
        
    except Exception as e:
        logger.error(f"Lifespan error: {e}", exc_info=True)
        raise e

# Create FastAPI app with lifespan
app = FastAPI(
    title="Vee Telegram Bot",
    description="Telegram webhook for Vee AI companion",
    lifespan=lifespan
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle incoming webhook requests from Telegram."""
    try:
        update_data = await request.json()
        
        # Validate update structure
        if not isinstance(update_data, dict):
            raise HTTPException(status_code=400, detail="Invalid update format")
        
        # Convert to python-telegram-bot Update object
        update = Update.de_json(update_data, None)
        if not update:
            raise HTTPException(status_code=400, detail="Invalid update data")
            
        # Process message
        await telegram_handler.handle_update(update, None)
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
