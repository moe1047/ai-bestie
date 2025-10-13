-- This script defines the database schema for Vee's long-term memory.
-- It uses normalized tables to store conversational context efficiently.

-- Drop tables in reverse order of dependency to prevent foreign key constraint errors.
DROP TABLE IF EXISTS sensing_data;
DROP TABLE IF EXISTS message;
DROP TABLE IF EXISTS session;
DROP TABLE IF EXISTS "user";

-- Stores permanent information about each unique user.
CREATE TABLE "user" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_chat_id INTEGER UNIQUE NOT NULL, -- The stable identifier from Telegram.
    name TEXT NOT NULL, -- User's display name.
    context TEXT, -- A JSON blob for long-term facts about the user (e.g., goals, preferences).
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Groups a continuous conversation into a single session.
CREATE TABLE session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When the session began.
    end_time TIMESTAMP, -- When the session ended (NULL if active).
    summary TEXT, -- An AI-generated summary of the conversation for quick context recall.
    FOREIGN KEY (user_id) REFERENCES "user" (id)
);

-- The central table logging every message and linking all context together.
CREATE TABLE message (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    role TEXT NOT NULL, -- 'user' or 'vee'.
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode TEXT -- The operational mode for this turn.
);

-- Stores the rich output from the perception model for each user message.
CREATE TABLE sensing_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL,
    -- Discourse
    dialogue_act TEXT,
    -- Intent
    primary_intent TEXT,
    sub_intent TEXT,
    -- Affect
    sentiment TEXT,
    valence REAL,
    arousal REAL,
    -- Safety
    risk_level TEXT NOT NULL,
    distress_hint INTEGER, -- Boolean
    -- Pragmatics
    inference TEXT,
    needs_clarification INTEGER, -- Boolean
    sarcasm_possible INTEGER, -- Boolean
    -- Fallback
    raw_output TEXT, -- Stores the full JSON output from the perception model.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES message (id)
);