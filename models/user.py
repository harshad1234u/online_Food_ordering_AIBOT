from database import get_db_connection

class User:
    @staticmethod
    def get_by_email(email):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT user_id, name, email, phone, address, is_admin FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user

    @staticmethod
    def create(name, email, hashed_password, phone, address):
        conn = get_db_connection()
        if not conn: return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)",
                (name, email, hashed_password, phone, address)
            )
            conn.commit()
            user_id = cursor.lastrowid
            return user_id
        except Exception as e:
            print(f"Error creating user: {e}")
            return None
        finally:
            cursor.close()
            conn.close()
