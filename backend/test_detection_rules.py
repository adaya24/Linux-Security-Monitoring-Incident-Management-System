import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from detection.engine import evaluate_process


def test_high_cpu():
    alerts = evaluate_process({"pid": 1, "name": "test", "cpu_percent": 96, "memory_mb": 100})
    assert any(a["event_type"] == "HIGH_CPU_USAGE" for a in alerts)


def test_elevated_cpu():
    alerts = evaluate_process({"pid": 1, "name": "test", "cpu_percent": 85, "memory_mb": 100})
    assert any(a["event_type"] == "ELEVATED_CPU_USAGE" for a in alerts)


def test_high_memory():
    alerts = evaluate_process({"pid": 1, "name": "test", "cpu_percent": 0, "memory_mb": 1100})
    assert any(a["event_type"] == "HIGH_MEMORY_USAGE" for a in alerts)


def test_elevated_memory():
    alerts = evaluate_process({"pid": 1, "name": "test", "cpu_percent": 0, "memory_mb": 600})
    assert any(a["event_type"] == "ELEVATED_MEMORY_USAGE" for a in alerts)


def test_normal_process():
    alerts = evaluate_process({"pid": 1, "name": "test", "cpu_percent": 10, "memory_mb": 100})
    assert alerts == []
