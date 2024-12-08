import psycopg2
from db import connect
from psycopg2.extras import DictCursor
from flask import current_app, jsonify


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
            with conn.cursor(cursor_factory=DictCursor) as cur:
                if "email" in kwargs:
                    query = f"SELECT * FROM {table_name} WHERE email = %s;"
                    cur.execute(query, (kwargs["email"],))
                elif "id" in kwargs:
                    query = f"SELECT * FROM {table_name} WHERE id = %s"
                    cur.execute(query, (kwargs["id"],))
                else:
                    return None
                result = cur.fetchone()

                return result
    except (psycopg2.DatabaseError, Exception) as ex:
        print(f"error retrieving data from table {table_name}: {ex}")
        return None


def insert_into_categories(table_name, **kwargs):
    """insert into categories table"""
    try:
        query = """INSERT INTO categories (name, description, parent_category_id) 
        VALUES (%s,%s,%s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id;"""
        with connect() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(
                query,
                (
                    kwargs.get("name"),
                    kwargs.get("description"),
                    kwargs.get("parent_category_id"),
                ),
            )
            result = cursor.fetchone()
            conn.commit()
            return result["id"] if result else None
    except (psycopg2.DatabaseError, Exception) as ex:
        print(f"error inserting into table {table_name}: {ex}")
        return None


def delete_records_from_table(table_name, **kwargs):
    query = f"DELETE FROM {table_name} WHERE id = %s"
    try:
        with connect() as conn:
            cursor = conn.cursor(cursor_factory=DictCursor)
            cursor.execute(query, (kwargs))
            conn.commit()
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500
