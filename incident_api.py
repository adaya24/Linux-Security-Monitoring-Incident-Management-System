
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection

router = APIRouter(prefix="/incidents", tags=["Incident Management"])

VALID_STATUSES = {
    "OPEN",
    "INVESTIGATING",
    "RESOLVED",
    "FALSE_POSITIVE"
}


class IncidentUpdate(BaseModel):
    status: str
    assigned_to: str | None = Field(default=None, max_length=100)


@router.get("")
def list_incidents():
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT incident_id, event_id, title, description,
                   severity, status, assigned_to, created_at, updated_at
            FROM incidents
            ORDER BY created_at DESC
            LIMIT 100
        """)
        return cursor.fetchall()
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


@router.get("/{incident_id}")
def get_incident(incident_id: int):
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM incidents WHERE incident_id = %s",
            (incident_id,)
        )
        incident = cursor.fetchone()

        if incident is None:
            raise HTTPException(status_code=404, detail="Incident not found")

        return incident
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


@router.put("/{incident_id}")
def update_incident(incident_id: int, update: IncidentUpdate):
    status = update.status.upper()

    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Choose one of: {sorted(VALID_STATUSES)}"
        )

    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE incidents
            SET status = %s, assigned_to = %s
            WHERE incident_id = %s
            """,
            (status, update.assigned_to, incident_id)
        )

        if cursor.rowcount == 0:
            cursor.execute(
                "SELECT incident_id FROM incidents WHERE incident_id = %s",
                (incident_id,)
            )
            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=404,
                    detail="Incident not found"
                )

        connection.commit()
        return {
            "message": "Incident updated",
            "incident_id": incident_id,
            "status": status,
            "assigned_to": update.assigned_to
        }

    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
