from database.connection import get_connection
def save_process_snapshot(processes):
    """Save a list of process snapshots to MariaDB."""
    if not processes:
        return 0

    connection = get_connection()

    try:
        cursor = connection.cursor()

        query = """
            INSERT INTO process_history
            (pid, process_name, username, status, cpu_percent, memory_mb)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = [
            (
                process["pid"],
                process["name"],
                process["username"],
                process["status"],
                process["cpu_percent"],
                process["memory_mb"]
            )
            for process in processes
        ]

        cursor.executemany(query, values)
        connection.commit()

        return cursor.rowcount

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()