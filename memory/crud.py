import sqlite3
import os
from contextlib import contextmanager
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.utils import get_buffer_string
from . import schemas
from llms.summarizer import summarize_session_narrative

# --- Database Connection ---


@contextmanager
def get_db_connection():
    """Provides a database connection as a context manager.
    Ensures the connection is closed after use.
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(dir_path, "vee_memory.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# --- Helper Functions ---


def _execute_insert(conn: sqlite3.Connection, query: str, params: tuple) -> int:
    """Executes an INSERT statement and returns the new row's ID."""
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    return cursor.lastrowid


# --- User Functions ---


def get_or_create_user(
    telegram_chat_id: int,
    name: str,
    context: Optional[Dict] = None,
) -> schemas.User:
    """Gets an existing user by telegram_chat_id or creates a new one."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM "user" WHERE telegram_chat_id = ?', (telegram_chat_id,)
        )
        user_data = cursor.fetchone()

        if user_data:
            return schemas.User(**user_data)

        context_str = json.dumps(context) if context else None
        query = 'INSERT INTO "user" (telegram_chat_id, name, context) VALUES (?, ?, ?)'
        params = (telegram_chat_id, name, context_str)
        user_id = _execute_insert(conn, query, params)

        cursor.execute('SELECT * FROM "user" WHERE id = ?', (user_id,))
        new_user_data = cursor.fetchone()
        return schemas.User(**new_user_data)


# --- Session Functions ---


def get_active_session(user_id: int, timeout_hours: int = 24) -> Optional[schemas.Session]:
    """Finds the most recent, active session for a user, expiring it if it's too old."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Find the latest session that hasn't been explicitly ended.
        query = "SELECT * FROM session WHERE user_id = ? AND end_time IS NULL ORDER BY start_time DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        session_data = cursor.fetchone()

        if not session_data:
            return None

        session = schemas.Session(**session_data)

        # Check the timestamp of the last message in the session.
        cursor.execute(
            "SELECT timestamp FROM message WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1",
            (session.id,),
        )
        last_message_timestamp_str = cursor.fetchone()

        last_activity_time = None
        if last_message_timestamp_str:
            last_activity_time = datetime.fromisoformat(last_message_timestamp_str[0])
        else:
            # If no messages, use the session's start time, which is already a datetime object.
            last_activity_time = session.start_time

        # If the last activity was too long ago, expire the session.
        if datetime.now() - last_activity_time > timedelta(hours=timeout_hours):
            end_session(session.id)
            return None  # Return None to signal that a new session should be created.

        return session

def get_last_closed_session(user_id: int) -> Optional[schemas.Session]:
    """Finds the most recently closed session for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "SELECT * FROM session WHERE user_id = ? AND end_time IS NOT NULL ORDER BY end_time DESC LIMIT 1"
        cursor.execute(query, (user_id,))
        session_data = cursor.fetchone()
        return schemas.Session(**session_data) if session_data else None


def end_session(session_id: int):
    """Closes a session by setting its end_time."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "UPDATE session SET end_time = ? WHERE id = ?"
        cursor.execute(query, (datetime.now().isoformat(), session_id))
        conn.commit()
        print(f"Session {session_id} has been ended.")


def create_session(user_id: int) -> schemas.Session:
    """Creates a new session for a user."""
    with get_db_connection() as conn:
        query = "INSERT INTO session (user_id) VALUES (?)"
        session_id = _execute_insert(conn, query, (user_id,))

        cursor = conn.cursor()
        cursor.execute("SELECT * FROM session WHERE id = ?", (session_id,))
        new_session_data = cursor.fetchone()
        return schemas.Session(**new_session_data)


# --- Data-Block Functions ---


def create_sensing_data(data: schemas.SensingData) -> int:
    """Inserts a new sensing_data record and returns its ID."""
    query = """INSERT INTO sensing_data (message_id, dialogue_act, primary_intent, sub_intent, sentiment, valence, arousal, risk_level, distress_hint, inference, needs_clarification, sarcasm_possible, raw_output)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    params = (
        data.message_id,
        data.dialogue_act,
        data.primary_intent,
        data.sub_intent,
        data.sentiment,
        data.valence,
        data.arousal,
        data.risk_level,
        data.distress_hint,
        data.inference,
        data.needs_clarification,
        data.sarcasm_possible,
        data.raw_output,
    )
    with get_db_connection() as conn:
        return _execute_insert(conn, query, params)


def get_recent_messages(session_id: int, limit: int = 20) -> List[HumanMessage | AIMessage]:
    """Retrieves the most recent messages for a session and converts them to LangChain message objects."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT id, role, content, timestamp
            FROM message
            WHERE id IN (
                SELECT id
                FROM message
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            )
            ORDER BY timestamp ASC
        """
        cursor.execute(query, (session_id, limit))
        rows = cursor.fetchall()

        messages = []
        # The rows are in descending order, so we reverse them to get the correct chronological order
        for row in reversed(rows):
            if row["role"] == "user":
                messages.append(HumanMessage(content=row["content"], additional_kwargs={"id": row["id"]}))
            elif row["role"] == "vee": # Changed from 'assistant' to 'vee'
                messages.append(AIMessage(content=row["content"], additional_kwargs={"id": row["id"]}))
        return messages

from zoneinfo import ZoneInfo

def get_recent_messages_as_string(session_id: int, limit: int = 20, timezone_str: str = "UTC") -> str:
    """Retrieves the most recent messages and formats them into a single string for the LLM context."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = """
            SELECT id, role, content, timestamp
            FROM message
            WHERE id IN (
                SELECT id
                FROM message
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            )
            ORDER BY timestamp ASC
        """
        cursor.execute(query, (session_id, limit))
        rows = cursor.fetchall()

        history_lines = []
        target_tz = ZoneInfo(timezone_str)
        for row in rows:
            # The datetime from the DB is already UTC-aware, so we can directly convert it
            ts_local = datetime.fromisoformat(row['timestamp']).astimezone(target_tz)
            formatted_ts = ts_local.strftime('%Y-%m-%d %H:%M:%S')
            role_str = 'Human' if row['role'] == 'user' else 'AI'
            history_lines.append(f"{role_str} (ID: {row['id']}, Timestamp: {formatted_ts}): {row['content']}")
        return "\n".join(history_lines)


def update_session_summary(session_id: int, summary: str):
    """Updates the summary for a given session."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        query = "UPDATE session SET summary = ? WHERE id = ?"
        cursor.execute(query, (summary, session_id))
        conn.commit()
        print(f"Updated summary for session {session_id}.")


# --- Message Function ---


def add_message(data: schemas.Message) -> int:
    """Adds a new message to the message table and returns its ID."""
    query = """INSERT INTO message (session_id, role, content, timestamp, mode)
             VALUES (?, ?, ?, ?, ?)"""
    params = (
        data.session_id,
        data.role,
        data.content,
        data.timestamp,
        data.mode,
    )
    with get_db_connection() as conn:
        return _execute_insert(conn, query, params)
