"""Script to run the Telegram bot server."""
import uvicorn
from dotenv import load_dotenv

def main():
    """Run the FastAPI server for Telegram bot."""
    load_dotenv()  # Load environment variables
    
    # Run the server
    uvicorn.run(
        "ui.telegram.app:app",
        host="0.0.0.0",  # Listen on all network interfaces
        port=8001,
        reload=True  # Enable auto-reload during development
    )

if __name__ == "__main__":
    main()
