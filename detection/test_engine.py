from engine import evaluate_process

sample = {
    "pid": 12345,
    "name": "demo_process",
    "cpu_percent": 85,
    "memory_mb": 600
}

alerts = evaluate_process(sample)

print("Test process:", sample["name"])
print("Generated alerts:")

for alert in alerts:
    print(alert["severity"], "-", alert["event_type"])
    print(alert["description"])
