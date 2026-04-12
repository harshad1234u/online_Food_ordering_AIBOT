import mysql.connector
from config import Config

def init_db():
    print("Connecting to MySQL...")
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        cursor = conn.cursor()
        
        # Read schema.sql
        with open('schema.sql', 'r') as f:
            sql_script = f.read()
            
        # Execute each statement
        for statement in sql_script.split(';'):
            if statement.strip():
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as err:
                    print(f"Error executing statement: {err}")
                    
        conn.commit()
        cursor.close()
        conn.close()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
