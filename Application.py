import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ctypes
import time
from datetime import datetime
import threading
import sqlite3
import csv
import socket  # For getting the IP address
import re  # Add this import for regex matching
import uuid  # Add this import for getting the MAC address
import sys
import os

# SMTP settings for Outlook
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL = "2300906009@st.aabu.edu.jo"  # Your email
EMAIL_PASSWORD = "Ghadyhamad2003"  # Your email password

# List of applications that require alerts
SOCIAL_MEDIA_APPS = [
    "Facebook", "Instagram", "Twitter", "WhatsApp", "TikTok", "Snapchat",
    "WhatsApp Web", "Spotify Free", "LinkedIn", "Telegram", "Pinterest",
    "Reddit", "Discord", "YouTube", "Netflix", "Hulu", "Amazon Prime Video",
    "Apple Music", "SoundCloud"
]

GAMES_APPS = [
    "Fortnite", "PUBG", "Minecraft", "League of Legends", "Valorant",
    "Roblox", "Call of Duty", "Apex Legends", "Overwatch", "World of Warcraft",
    "Clash of Clans", "Candy Crush"
]

DB_NAME = "application.db"
CSV_FILE = "application.csv"
stop_monitoring = False

# Windows API functions
EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

# Force UTF-8 encoding for the console
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS windows_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            window_title TEXT,
            status TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Log data to the database and CSV
def log_to_db(window_title, status, alert_flag):
    try:
        # Log to database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO windows_log (window_title, status) VALUES (?, ?)', (window_title, status))
        conn.commit()

        # Get the last inserted row ID and timestamp
        last_id = cursor.lastrowid
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Log to CSV immediately with utf-8 encoding
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([last_id, window_title, status, timestamp, alert_flag])

        conn.close()

    except Exception as e:
        print(f"Error logging to database and CSV: {e}", flush=True)

# Function to send an email alert
def send_email_alert(window_title, status):
    try:
        # Get the IP address
        ip_address = socket.gethostbyname(socket.gethostname())
        mac_address = get_mac_address()  # Get the MAC address

        subject = "Alert: Restricted Application Detected"
        body = (
            f"The application '{window_title}' was {status} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.\n"
            f"Device IP Address: {ip_address}\n"
            f"Device MAC Address: {mac_address}"
        )

        # Set up the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL
        msg["To"] = EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send the email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD)
            server.sendmail(EMAIL, EMAIL, msg.as_string())

        print(f"[ALERT] Email sent successfully to '{EMAIL}' for application '{window_title}' with IP '{ip_address}' and MAC '{mac_address}'.", flush=True)

    except Exception as e:
        print(f"Error sending email: {e}", flush=True)

# Function to detect key press
def detect_key_press():
    global stop_monitoring
    print("Press Enter to stop monitoring...\n", flush=True)  # Ensure the prompt is flushed
    input()  
    stop_monitoring = True

# Function to get all visible windows
def get_open_windows():
    windows = {}

    def foreach_window(hwnd, lParam):
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                window_title = buff.value
                if window_title:  # Only add non-empty titles
                    windows[window_title] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)
    return windows

# Add the new invalid pattern
EXEC = r"\b(?:C:\\Program Files(?: \(x86\))?\\[^\s\\]+\\[^\s\\]+\.exe)\b"
URLs = r"\b(?:chrome|firefox|edge|safari|opera)[^\s]*\.(exe|dll|json|db)\b"
cmd = r"\b(cmd\.exe|powershell\.exe|bash|sh|zsh|terminal|cmd)\b"

def monitor_windows():
    global stop_monitoring
    previous_windows = get_open_windows()
    alerted_apps = set()  # Track applications that have been alerted
    print("Monitoring open windows. Press Enter to stop.\n", flush=True)

    while not stop_monitoring:
        try:
            current_windows = get_open_windows()

            # Display currently open windows
            print("\n---- Currently Open Windows ----", flush=True)
            for title, open_time in current_windows.items():
                print(f"- {title.encode('utf-8', 'replace').decode()} | Opened at: {open_time}", flush=True)

                # Check if the application is restricted
                if any(app.lower() in title.lower() for app in SOCIAL_MEDIA_APPS + GAMES_APPS) or re.search(EXEC, title) or re.search(URLs, title) or re.search(cmd, title):
                    if title not in alerted_apps:  # Check if the alert has not been sent
                        log_to_db(title, "Opened", 1)  # Log with alert
                        send_email_alert(title, "Opened")  # Send email alert
                        show_user_alert(title)  # Show alert to the user
                        alerted_apps.add(title)  # Add the app to the alert list
                    else:
                        log_to_db(title, "Opened", 0)  # Log without alert
                else:
                    log_to_db(title, "Opened", 0)  # Log without alert
            print("--------------------------------\n", flush=True)

            # Check for closed applications
            closed_apps = [title for title in alerted_apps if title not in current_windows]
            if closed_apps:
                print("---- Closed Restricted Applications ----", flush=True)
                for app in closed_apps:
                    close_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"- {app} | Closed at: {close_time} (Sending alert for closure...)", flush=True)
                    log_to_db(app, "Closed", 1)  # Log with alert
                    send_email_alert(app, "Closed")
                    alerted_apps.remove(app)  # Remove the app from the alert list
                print("--------------------------------\n", flush=True)

            # Update the previous windows list
            previous_windows = current_windows

            # Wait for 10 seconds before checking again
            time.sleep(10)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.", flush=True)
            break

def show_user_alert(window_title):
    """
    Display a warning message to the user about the restricted application.
    """
    ctypes.windll.user32.MessageBoxW(
        0,
        f"The application '{window_title}' is restricted. Please close it immediately.",
        "Restricted Application Alert",
        0x30  # MB_ICONWARNING
    )

def get_mac_address():
    """
    Retrieve the MAC address of the device.
    """
    mac = uuid.getnode()
    mac_address = ':'.join(f'{(mac >> i) & 0xFF:02x}' for i in range(0, 8 * 6, 8))[::-1]
    return mac_address

def main():
    # Initialize the database
    init_db()

    # Create the CSV file with headers if it doesn't exist
    try:
        with open(CSV_FILE, mode="a", newline="") as file:
            # Check if the file is empty, and if so, add headers
            if file.tell() == 0:
                writer = csv.writer(file)
                writer.writerow(["ID", "Window Title", "Status", "Timestamp", "Alert"])  # Write header
    except Exception as e:
        print(f"Error initializing CSV file: {e}", flush=True)

    # Start a thread to monitor windows
    monitor_thread = threading.Thread(target=monitor_windows)
    monitor_thread.start()

    # Start the key press detection in the main thread
    try:
        detect_key_press()
    except KeyboardInterrupt:
        global stop_monitoring
        stop_monitoring = True
        print("\nMonitoring stopped by user.", flush=True)

    # Wait for the monitor thread to finish
    monitor_thread.join()

# Call the main function
if __name__ == "__main__":
    main()