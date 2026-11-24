import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection


def create_incident_from_event(event_id):
    """Create one incident from an existing security event."""
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)

        # Verify that the event exists.
        cursor.execute(
            """
            SELECT id, pid, event_type, severity, description
            FROM security_events
            WHERE id = %s
            """,
            (event_id,)
        )
        event = cursor.fetchone()

        if event is None:
            return None

        # Avoid creating a duplicate incident for the same event.
        cursor.execute(
            "SELECT incident_id FROM incidents WHERE event_id = %s",
            (event_id,)
        )
        existing = cursor.fetchone()

        if existing:
            return existing["incident_id"]

        cursor.execute(
            """
            INSERT INTO incidents
                (event_id, title, description, severity, status)
            VALUES (%s, %s, %s, %s, 'OPEN')
            """,
            (
                event["id"],
                event["event_type"],
                event["description"],
                event["severity"]
            )
        )

        connection.commit()
        return cursor.lastrowid

    except Exception:
        connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
