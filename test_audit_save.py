
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = PROJECT_DIR / "backend"

sys.path.insert(0, str(PROJECT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

from auditing.auditor import run_audit
from database.audit_repository import save_audit_results


if __name__ == "__main__":
    results = run_audit()

    try:
        saved = save_audit_results(results)
        print(f"Audit findings collected: {len(results)}")
        print(f"Audit findings saved: {saved}")

    except Exception as error:
        print("Could not save audit results:", error)

