import psycopg2
from server.db import connect


def insert_into_users(table_name, username, email, password):
    """insert user data into users to register"""
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                query = f"""
                            INSERT INTO {table_name}
                            (username, email, password) 
                            VALUES (%s, %s, %s) 
                            ON CONFLICT (email) DO NOTHING; 
                        """
                cur.execute(query, (username, email, password))
                conn.commit()
    except (psycopg2.DatabaseError, Exception) as err:
        print(f"error insering into table {table_name}: {err}")


def select_from_table(table_name, email):
    """retrieve user data from database for auth and login"""
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                query = f"SELECT * FROM {table_name} WHERE email = %s;"
                cur.execute(query, (email,))
                result = cur.fetchone()
                return result
    except (psycopg2.DatabaseError, Exception) as ex:
        print(f"error retrieving data from table {table_name}: {ex}")
        return None
