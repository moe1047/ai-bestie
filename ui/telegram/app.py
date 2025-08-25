"""FastAPI application for Telegram webhook handler for Vee AI companion."""
import logging
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update
from ui.telegram.client import TelegramClient
from ui.telegram.handler import TelegramHandler
from ui.telegram.config import TelegramSettings
import aiosqlite
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load settings
settings = TelegramSettings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events, including checkpointer lifecycle."""
    # Use an absolute path to ensure the database file is found
    db_path = Path(__file__).parent.parent.parent / "data" / "vee_short_memory.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Connect to the database directly
    conn = await aiosqlite.connect(db_path.resolve())
    try:
        checkpointer = AsyncSqliteSaver(conn=conn)
        logger.info("Database connection opened.")

        # Initialize clients and handlers
        telegram_client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        telegram_handler = TelegramHandler(telegram_client, checkpointer)

        # Store handler in app state to make it accessible in routes
        app.state.telegram_handler = telegram_handler

        # Startup: verify bot and set webhook
        async with telegram_client.get_session() as session:
            me = await telegram_client.get_me()
            logger.info(f"Bot authorized as: {me.get('username')}")

        result = await telegram_client.set_webhook(settings.WEBHOOK_URL)
        if not result.get("ok"):
            raise Exception(f"Failed to set webhook: {result}")

        logger.info("Webhook set successfully")
        yield

    finally:
        # Shutdown: clean up webhook and database connection
        await telegram_client.delete_webhook()
        logger.info("Webhook deleted successfully")
        await conn.close()
        logger.info("Database connection closed.")

# Create FastAPI app with lifespan
app = FastAPI(
    title="Vee",
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
            
        # Process message using the handler from app state
        telegram_handler = request.app.state.telegram_handler
        await telegram_handler.handle_update(update, None)
        return {"ok": True}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
