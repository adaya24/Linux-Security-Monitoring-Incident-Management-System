import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from database.connection import get_connection


def evaluate_process(process):
    """Generate rule-based alerts from process resource usage."""
    alerts = []

    cpu = float(process.get("cpu_percent", 0))
    memory = float(process.get("memory_mb", 0))
    pid = int(process["pid"])
    name = process.get("name", "Unknown")

    if cpu > 95:
        alerts.append({
            "pid": pid,
            "event_type": "HIGH_CPU_USAGE",
            "severity": "HIGH",
            "description": (
                f"Process {name} (PID {pid}) is using "
                f"{cpu:.2f}% CPU. Investigate if sustained."
            )
        })
    elif cpu > 80:
        alerts.append({
            "pid": pid,
            "event_type": "ELEVATED_CPU_USAGE",
            "severity": "MEDIUM",
            "description": (
                f"Process {name} (PID {pid}) is using "
                f"{cpu:.2f}% CPU."
            )
        })

    # These are initial, configurable per-process memory thresholds.
    if memory > 1024:
        alerts.append({
            "pid": pid,
            "event_type": "HIGH_MEMORY_USAGE",
            "severity": "HIGH",
            "description": (
                f"Process {name} (PID {pid}) is using "
                f"{memory:.2f} MB of resident memory."
            )
        })
    elif memory > 512:
        alerts.append({
            "pid": pid,
            "event_type": "ELEVATED_MEMORY_USAGE",
            "severity": "MEDIUM",
            "description": (
                f"Process {name} (PID {pid}) is using "
                f"{memory:.2f} MB of resident memory."
            )
        })

    return alerts



def save_alerts(alerts):
    """Save new active alerts and create incidents for them."""
    if not alerts:
        return 0

    from incidents.manager import create_incident_from_event

    connection = get_connection()
    cursor = None

    try:
        cursor = connection.cursor(dictionary=True)
        saved = 0

        for alert in alerts:
            # Skip an alert if the same PID and rule are already active.
            cursor.execute(
                """
                SELECT id
                FROM security_events
                WHERE pid = %s
                  AND event_type = %s
                  AND status IN ('OPEN', 'INVESTIGATING')
                LIMIT 1
                """,
                (alert["pid"], alert["event_type"])
            )

            if cursor.fetchone():
                continue

            cursor.execute(
                """
                INSERT INTO security_events
                    (pid, event_type, severity, description)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    alert["pid"],
                    alert["event_type"],
                    alert["severity"],
                    alert["description"]
                )
            )

            event_id = cursor.lastrowid
            saved += 1

            # Create the corresponding incident.
            cursor.execute(
                """
                INSERT INTO incidents
                    (event_id, title, description, severity, status)
                VALUES (%s, %s, %s, %s, 'OPEN')
                """,
                (
                    event_id,
                    alert["event_type"],
                    alert["description"],
                    alert["severity"]
                )
            )

        connection.commit()
        return saved

    except Exception:
        connection.rollback()
        raise

    finally:
        if cursor is not None:
            cursor.close()
        connection.close()
