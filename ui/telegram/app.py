"""FastAPI application for Telegram webhook handler for Vee AI companion."""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update
from ui.telegram.client import TelegramClient
from ui.telegram.handler import TelegramHandler
from ui.telegram.config import TelegramSettings
import aiosqlite
from pathlib import Path
from memory import crud

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Load settings
settings = TelegramSettings()

# --- Background Worker for DB Writes ---

db_write_queue = asyncio.Queue()

async def db_worker():
    """Worker that processes database write operations from a queue."""
    logger.info("DB worker started.")
    while True:
        try:
            # Wait for a task
            db_func, args, kwargs = await db_write_queue.get()
            
            # Execute the database function
            with crud.get_db_connection() as conn:
                db_func(conn, *args, **kwargs)
            
            # Mark the task as done
            db_write_queue.task_done()
            logger.info(f"DB task {db_func.__name__} completed.")

        except asyncio.CancelledError:
            logger.info("DB worker stopping.")
            break
        except Exception as e:
            logger.error(f"Error in DB worker: {e}", exc_info=True)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events, including checkpointer lifecycle."""
    # Use an absolute path to ensure the database file is found
    db_path = Path(__file__).parent.parent.parent / "data" / "vee_short_memory.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = await aiosqlite.connect(db_path.resolve())
    logger.info("Database connection opened.")

    # Start the background DB worker
    db_worker_task = asyncio.create_task(db_worker())

    try:
        # Initialize clients and handlers
        telegram_client = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
        # Pass the queue to the handler
        telegram_handler = TelegramHandler(telegram_client, db_write_queue)

        # Store handler in app state to make it accessible in routes
        app.state.telegram_handler = telegram_handler

        # Connect the client
        await telegram_client.connect()

        # Startup: verify bot and set webhook
        me = await telegram_client.get_me()
        logger.info(f"Bot authorized as: {me.get('username')}")

        result = await telegram_client.set_webhook(settings.WEBHOOK_URL)
        if not result.get("ok"):
            raise Exception(f"Failed to set webhook: {result}")

        logger.info("Webhook set successfully")
        yield

        # --- Shutdown ---

    finally:
        # Shutdown: clean up webhook, database connection, and worker
        if 'telegram_client' in locals() and telegram_client:
            await telegram_client.delete_webhook()
            await telegram_client.close()
            logger.info("Webhook deleted successfully")

        # Signal the worker to stop and wait for it to finish
        if 'db_worker_task' in locals():
            db_worker_task.cancel()
            try:
                await db_worker_task
            except asyncio.CancelledError:
                pass

        if 'conn' in locals() and conn:
            await conn.close()
            logger.info("Database connection closed.")


# Create FastAPI app with lifespan
app = FastAPI(
    title="Vee", description="Telegram webhook for Vee AI companion", lifespan=lifespan
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


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
