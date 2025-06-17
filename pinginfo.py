import os
import socket
import datetime
import time
import sqlite3
import csv

DB_NAME = "connectivity_log.db"
CSV_FILE = "connectivity_logs.csv"

# Create DB & Table
def create_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Drop the table if it exists (optional, only if you want to reset the table)
    cursor.execute('DROP TABLE IF EXISTS connectivity')
    # Create the table with the correct schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS connectivity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            label TEXT,
            duration TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Insert status into the database and write to CSV
def log_status(status, duration="0"):
    try:
        # Determine the label based on the status
        label = "good" if status == "connected" else "bad"

        # Log to database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO connectivity (status, label, duration) VALUES (?, ?, ?)', (status, label, duration))
        conn.commit()

        # Get the current timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log to CSV file (append mode)
        file_exists = os.path.isfile(CSV_FILE)
        with open(CSV_FILE, mode='a', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Write the header only if the file is newly created
            if not file_exists:
                writer.writerow(["ID", "Timestamp", "Status", "Label", "Duration"])
            writer.writerow([cursor.lastrowid, timestamp, status, label, duration])

        conn.close()
        print(f"Logged status: {status} ({label}) at {timestamp} with duration: {duration}", flush=True)
    except Exception as e:
        print(f"Failed to log status: {e}", flush=True)

# Export to CSV
def export_logs_to_csv(filename="connectivity_logs.csv"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM connectivity ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No records found in database to export.", flush=True)
        return

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Timestamp", "Status", "Label", "Duration"])  # Header
        writer.writerows(rows)

    print(f"Exported {len(rows)} records to {filename}", flush=True)

# Ping function to check connectivity
def ping():
    try:
        socket.setdefaulttimeout(3)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        host = "8.8.8.8"
        port = 53
        server_address = (host, port)
        s.connect(server_address)
    except OSError as error:
        return False
    else:
        s.close()
        return True

# Calculate time difference
def calculate_time(start, stop):
    difference = stop - start
    seconds = float(str(difference.total_seconds()))
    return str(datetime.timedelta(seconds=seconds)).split(".")[0]

# First connectivity check
def first_check():
    if ping():
        live = "\nCONNECTION ACQUIRED\n"
        print(live, flush=True)
        connection_acquired_time = datetime.datetime.now()
        acquiring_message = "connection acquired at: " + str(connection_acquired_time).split(".")[0]
        print(acquiring_message, flush=True)
        return True
    else:
        not_live = "\nCONNECTION NOT ACQUIRED\n"
        print(not_live, flush=True)
        return False

# Main function
def main():
    create_db()

    # Ensure the CSV file exists and has a header
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Timestamp", "Status", "Label", "Duration"])  # Write header

    monitor_start_time = datetime.datetime.now()
    monitoring_date_time = "Monitoring started at: " + str(monitor_start_time).split(".")[0]

    if first_check():
        print(monitoring_date_time, flush=True)
        log_status("connected")  # Log initial connection status
    else:
        while True:
            if not ping():
                time.sleep(1)
            else:
                first_check()
                print(monitoring_date_time, flush=True)
                log_status("connected")  # Log connection acquired
                break

    while True:
        if ping():
            time.sleep(5)
        else:
            down_time = datetime.datetime.now()
            fail_msg = "Disconnected at: " + str(down_time).split(".")[0]
            print(fail_msg, flush=True)
            log_status("disconnected")  # Log disconnection status

            while not ping():
                time.sleep(1)

            up_time = datetime.datetime.now()
            uptime_message = "Connected again: " + str(up_time).split(".")[0]
            down_time_duration = calculate_time(down_time, up_time)
            unavailability_time = "Connection was unavailable for: " + down_time_duration

            print(uptime_message, flush=True)
            print(unavailability_time, flush=True)
            log_status("connected", down_time_duration)  # Log reconnection status with duration

if __name__ == "__main__":
    main()