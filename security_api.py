
import sys
from pathlib import Path

from fastapi import APIRouter

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from process_monitor import get_processes
from database.connection import get_connection
from detection.engine import evaluate_process, save_alerts

router = APIRouter(prefix="/security", tags=["Security"])


@router.post("/scan")
def scan_processes():
    """Evaluate current processes and save generated alerts."""
    processes = get_processes()
    alerts = []

    for process in processes:
        alerts.extend(evaluate_process(process))

    saved = save_alerts(alerts)

    return {
        "processes_scanned": len(processes),
        "alerts_generated": len(alerts),
        "alerts_saved": saved,
        "alerts": alerts
    }


@router.get("/events")
def list_security_events():
    """Return the most recent security events."""
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, pid, event_type, severity,
                   description, status, created_at
            FROM security_events
            ORDER BY created_at DESC
            LIMIT 100
        """)
        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
