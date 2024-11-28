import psycopg2
from config.config import lead_config
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="  %(name)s - %(levelname)s - %(message)s",
    # logging.debug
    # logging.info
    # logging.warning
    # logging.error
    # logging.critical
)


DB_CONFIG = lead_config("database.ini", "postgresql")


def connect():
    """establishing connection with database"""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            logging.info("connected to database successfully")

            # with conn.cursor() as cursor:
            #     cursor.execute("select * from users;")
            #     users = cursor.fetchall()
            #     print(users)
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"failed connecting to database: {error}")
