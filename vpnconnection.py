import csv
import os
import sqlite3
import socket
import requests
from datetime import datetime
import sys

# Ensure UTF-8 encoding is used
if not sys.stdout.encoding.lower().startswith('utf'):
    sys.stdout = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    sys.stderr = open(sys.stderr.fileno(), mode='w', encoding='utf-8', buffering=1)

# Constants
DB_FILE = "vpn_logs.db"
CSV_FILE = "vpn_logs.csv"


def print_header(title):
    print("=" * 40, flush=True)
    print(title, flush=True)
    print("=" * 40, flush=True)


def get_ip_address():
    try:
        response = requests.get("https://api.ipify.org")
        ip = response.text.strip()
        print(f"Detected IP address: {ip}", flush=True)
        return ip
    except requests.RequestException as e:
        print(f"Failed to get IP address: {e}", flush=True)
        return "Unknown"


def is_vpn(ip):
    # Placeholder VPN check - in real use, you'd query a VPN detection API
    known_vpn_ips = ["185.216.140.10", "185.220.101.1"]
    print(f"Checking if IP {ip} is in known VPN list...", flush=True)
    return ip in known_vpn_ips


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vpn_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ip_address TEXT,
            vpn_status TEXT,
            status TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_to_db(ip, vpn_status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status = "Suspicious" if vpn_status == "Using VPN" else "Clean"

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vpn_logs (timestamp, ip_address, vpn_status, status)
        VALUES (?, ?, ?, ?)
    """, (timestamp, ip, vpn_status, status))
    conn.commit()
    conn.close()

    try:
        new_file = not os.path.exists(CSV_FILE)
        with open(CSV_FILE, mode="a", newline="") as file:
            writer = csv.writer(file)
            if new_file:
                writer.writerow(["ID", "Timestamp", "IP Address", "VPN Status", "Status"])
            writer.writerow([None, timestamp, ip, vpn_status, status])
    except Exception as e:
        print(f"Failed to write to CSV: {e}", flush=True)


def run_vpn_check():
    print_header("VPN IP Address CHECKER")
    init_db()
    ip = get_ip_address()
    if ip == "Unknown":
        print("Could not check VPN status due to IP fetch error.", flush=True)
        return

    if is_vpn(ip):
        print("VPN Detected \U00002705", flush=True)
        vpn_status = "Using VPN"
    else:
        print("No VPN Detected \U0000274C", flush=True)
        vpn_status = "Not Using VPN"

    log_to_db(ip, vpn_status)


if __name__ == "__main__":
    run_vpn_check()
