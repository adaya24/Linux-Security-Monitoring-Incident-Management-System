
import sys
from pathlib import Path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
from database.connection import get_connection
def save_audit_results(results):
    """Save security audit findings to MariaDB."""
    if not results:
        return 0

    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO audit_results
            (check_type, status, severity, description, recommendation)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = [
            (
                result["check"],
                result["status"],
                result["severity"],
                result["details"],
                result.get(
                    "recommendation",
                    "Review this finding and verify the system configuration."
                )
            )
            for result in results
        ]

        cursor.executemany(query, values)
        connection.commit()
        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

