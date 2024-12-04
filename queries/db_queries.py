import psycopg2
from db import connect


def insert_into_users(table_name, username, email, password, role):
    """insert user data into users to register"""
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                query = f"""
                            INSERT INTO {table_name}
                            (username, email, password, role) 
                            VALUES (%s, %s, %s, %s) 
                            ON CONFLICT (email) DO NOTHING; 
                        """
                cur.execute(query, (username, email, password, role))
                conn.commit()

                if cur.rowcount > 0:
                    print("success with insertion")
                    return True
                else:
                    print("insertion fail. conflict on email")
                    return False
    except (psycopg2.DatabaseError, Exception) as err:
        print(f"error insering into table {table_name}: {err}")
        return False


def select_from_table(table_name, **kwargs):
    """retrieve user data from database for auth and login"""
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                if "email" in kwargs:
                    query = f"SELECT * FROM {table_name} WHERE email = %s;"
                    cur.execute(query, (kwargs["email"],))
                elif "id" is kwargs:
                    query = f"SELECT * FROM {table_name} WHERE id = %s"
                else:
                    return None
                result = cur.fetchone()

                return result
    except (psycopg2.DatabaseError, Exception) as ex:
        print(f"error retrieving data from table {table_name}: {ex}")
        return None