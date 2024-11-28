import psycopg2
from config.config import lead_config

DB_CONFIG = lead_config("database.ini", "postgresql")


def connect():
    """establishing connection with database"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            print("connected to database successfully")
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"failed connecting to database: {error}")
