
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from incidents.manager import create_incident_from_event
from database.connection import get_connection


connection = get_connection()
cursor = connection.cursor()

try:
    cursor.execute(
        "SELECT id FROM security_events ORDER BY id DESC LIMIT 1"
    )
    row = cursor.fetchone()
finally:
    cursor.close()
    connection.close()

if row is None:
    print("No security events exist yet. Run a security scan first.")
else:
    incident_id = create_incident_from_event(row[0])

    if incident_id is None:
        print("The security event was not found.")
    else:
        print("Incident created or already exists.")
        print("Incident ID:", incident_id)
