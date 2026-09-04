"""Create or restore the bundled local demonstration database."""

from offline_database import DATABASE_PATH, initialize_database


if __name__ == "__main__":
    initialize_database()
    print(f"Local database ready: {DATABASE_PATH}")
