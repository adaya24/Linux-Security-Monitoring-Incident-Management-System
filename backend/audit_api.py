import sys
from pathlib import Path

from fastapi import APIRouter

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from auditing.auditor import run_audit
from database.audit_repository import save_audit_results
from database.connection import get_connection

router = APIRouter(prefix="/audit", tags=["Security Audit"])


@router.post("/run")
def run_security_audit():
    results = run_audit()
    saved = save_audit_results(results)

    return {
        "findings_collected": len(results),
        "findings_saved": saved,
        "results": results
    }


@router.get("/results")
def get_audit_results():
    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT audit_id, check_type, status, severity,
                   description, recommendation, checked_at
            FROM audit_results
            ORDER BY audit_id DESC
            LIMIT 100
        """)
        return cursor.fetchall()

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
