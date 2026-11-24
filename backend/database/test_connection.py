
from connection import get_connection

try:
    conn = get_connection()
    print("Database connection successful!")

    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")

    print("Tables found:")
    for table in cursor.fetchall():
        print("-", table[0])

    cursor.close()
    conn.close()

except Exception as error:
    print("Database connection failed:", error)
