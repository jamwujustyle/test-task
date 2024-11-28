import psycopg2


def connect():
    conn = psycopg2.connect(
        dbname="test_task",
        host="localhost",
        password="0880",
        user="postgres",
        port=5432,
    )
    try:
        print("connected successfully")
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"error connecting: {error}")


connect()
