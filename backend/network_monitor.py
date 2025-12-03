# backend/network_monitor.py
import psutil
import time
import os
import socket
import requests
from datetime import datetime
from typing import Dict, List, Any

# --- Configuration ---
MONITORING_INTERVAL_SECONDS = 5
MAX_REPORTS = 999999  # or set to 5 while testing
SERVER_URL = "http://localhost:8005/events"
REQUEST_TIMEOUT = 1.5  # seconds


def get_process_path_map() -> Dict[int, str]:
    pid_to_path = {}
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        try:
            pid = proc.info['pid']
            exe_path = proc.info.get('exe') or proc.info.get('name')
            if pid and exe_path:
                pid_to_path[pid] = exe_path
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return pid_to_path


def list_active_tcp_connections(pid_map: Dict[int, str]) -> List[Dict[str, Any]]:
    connections = []
    for conn in psutil.net_connections(kind='tcp'):
        if conn.status == psutil.CONN_ESTABLISHED or conn.status == psutil.CONN_LISTEN:
            remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A"
            if conn.status == psutil.CONN_ESTABLISHED and remote_addr == "N/A":
                continue
            pid = conn.pid
            local_addr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "N/A"
            connections.append({
                "pid": pid if pid else "N/A",
                "status": conn.status,
                "local_addr": local_addr,
                "remote_addr": remote_addr,
                "process_path": pid_map.get(pid, "Unknown/System Process")
            })
    return connections


def print_connection_report(report_data: List[Dict[str, Any]]):
    import pandas as pd
    if not report_data:
        print("No active established or listening TCP connections found.")
        return
    df = pd.DataFrame(report_data)
    df['Process Name'] = df['process_path'].apply(lambda x: os.path.basename(x))
    df = df[['Process Name', 'pid', 'status', 'local_addr', 'remote_addr', 'process_path']]
    df.columns = ["Process Name", "PID", "Status", "Local Endpoint", "Remote Endpoint", "Executable Path"]
    print("\n" + "=" * 100)
    print(f"Active TCP Connection Report | Time: {time.ctime()}")
    print("=" * 100)
    print(df.to_string(index=False))
    print("=" * 100 + "\n")


def send_event(payload: dict):
    try:
        requests.post(SERVER_URL, json=payload, timeout=REQUEST_TIMEOUT)
    except Exception:
        pass


if __name__ == "__main__":
    try:
        import pandas as pd
    except ImportError:
        print("Error: This script requires the 'pandas' library. Run pip install pandas")
        exit()

    print("Starting network connection monitor. Press Ctrl+C to stop.")
    report_count = 0
    while True:
        try:
            pid_map = get_process_path_map()
            connections = list_active_tcp_connections(pid_map)

            # Print local human-friendly table
            print_connection_report(connections)

            # Send each connection to central server
            hostname = socket.gethostname()
            ts = datetime.utcnow().isoformat() + "Z"
            for conn in connections:
                process_path = conn.get("process_path", "")
                proc_name = os.path.basename(process_path) if process_path else ""
                payload = {
                    "host": hostname,
                    "timestamp": ts,
                    "process": proc_name,
                    "pid": conn.get("pid"),
                    "local": conn.get("local_addr"),
                    "remote": conn.get("remote_addr"),
                    "status": conn.get("status"),
                    "exe_path": process_path,
                    "label": "Normal",
                    "score": None
                }
                send_event(payload)

            time.sleep(MONITORING_INTERVAL_SECONDS)
            report_count += 1

        except KeyboardInterrupt:
            print("\nMonitoring stopped by user.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break
