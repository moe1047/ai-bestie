import sqlite3
import os


def initialize_database(db_path: str, schema_path: str):
    """
    Initializes the database by creating tables from a schema file.

    Args:
        db_path (str): The path to the SQLite database file.
        schema_path (str): The path to the .sql schema file.
    """
    print(f"[DB Setup] Database path: {db_path}")
    print(f"[DB Setup] Schema path: {schema_path}")

    if not os.path.exists(schema_path):
        print(f"[DB Setup] Error: Schema file not found at {schema_path}")
        return

    try:
        # Connect to the SQLite database. It will be created if it doesn't exist.
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("[DB Setup] Reading schema...")
        with open(schema_path, "r") as f:
            sql_script = f.read()

        print("[DB Setup] Executing SQL script to create tables...")
        cursor.executescript(sql_script)

        conn.commit()
        print("[DB Setup] Tables created successfully.")

    except sqlite3.Error as e:
        print(f"[DB Setup] An error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("[DB Setup] Database connection closed.")


def main():
    """Main function to run the database setup process."""
    # Get the directory of the current script
    dir_path = os.path.dirname(os.path.realpath(__file__))

    # Define paths for the database and schema files
    db_path = os.path.join(dir_path, "vee_memory.db")
    schema_path = os.path.join(dir_path, "schema.sql")

    initialize_database(db_path, schema_path)


if __name__ == "__main__":
    main()
