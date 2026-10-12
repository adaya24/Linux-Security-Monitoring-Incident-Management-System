import psutil
import time


def get_processes():
    """Collect process information and CPU usage."""
    processes = list(
        psutil.process_iter(
            ["pid", "name", "username", "status", "memory_info"]
        )
    )

    # First measurement initializes CPU counters
    for process in processes:
        try:
            process.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Allow time for CPU usage to be measured
    time.sleep(1)

    results = []

    for process in processes:
        try:
            info = process.info
            memory = info.get("memory_info")
            cpu = process.cpu_percent(interval=None)

            results.append({
                "pid": info["pid"],
                "name": info["name"] or "Unknown",
                "username": info["username"] or "Unknown",
                "status": info["status"],
                "cpu_percent": round(cpu, 2),
                "memory_mb": round(memory.rss / (1024 * 1024), 2)
                if memory else 0
            })

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return results


if __name__ == "__main__":
    print("Linux Security Monitor - Process Monitor")
    print("-" * 100)

    print(
        f"{'PID':<8}{'Process':<23}{'User':<14}"
        f"{'Status':<14}{'CPU %':<10}{'Memory MB':<12}"
    )
    print("-" * 100)

    for process in get_processes():
        print(
            f"{process['pid']:<8}"
            f"{process['name'][:21]:<23}"
            f"{process['username'][:12]:<14}"
            f"{process['status']:<14}"
            f"{process['cpu_percent']:<10.2f}"
            f"{process['memory_mb']:<12.2f}"
        )

