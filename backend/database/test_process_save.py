
import sys
from pathlib import Path

# Add the backend directory to Python's import path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from process_monitor import get_processes
from database.process_repository import save_process_snapshot

try:
    processes = get_processes()
    saved = save_process_snapshot(processes)

    print(f"Processes collected: {len(processes)}")
    print(f"Rows inserted: {saved}")

except Exception as error:
    print("Could not save process snapshots:", error)

