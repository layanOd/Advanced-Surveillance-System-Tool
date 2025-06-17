from pynput import mouse, keyboard
import datetime
import sqlite3
import csv
import os
import sys
from collections import defaultdict

# Force UTF-8 encoding for the console
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

# ملفات التخزين
LOG_FILE = "mouse_event.txt"
DB_NAME = "mouse_events.db"
CSV_FILE = "mouse_event.csv"
OUTPUT_CSV_FILE = "mouse_event_with_idle.csv"
SUMMARY_CSV_FILE = "idle_summary_per_day.csv"

# ثوابت
LOG_INTERVAL = 2  # ثواني بين تسجيل تحركات الماوس
MOVE_THRESHOLD = 100  # تغيير المسافة في التحريك لتسجيل حركة جديدة
SCROLL_THRESHOLD = 1
CLICK_DEBOUNCE = 1  # ثواني بين تسجيل نقرات
IDLE_THRESHOLD = 60  # خمول يُحسب بعد 60 ثانية

# الحالة العامة
stop_flag = False
last_logged_position = None
last_logged_move_time = None
last_click_time = None
last_event_time = None  # آخر حدث مسجل (للخمول)

def get_local_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mouse_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_idle_summary(date, from_time, to_time, duration):
    file_exists = os.path.isfile(SUMMARY_CSV_FILE)
    write_header = not file_exists or os.stat(SUMMARY_CSV_FILE).st_size == 0

    with open(SUMMARY_CSV_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["Date", "From", "To", "Duration (Minutes)"])
        writer.writerow([date, from_time, to_time, duration])

def log_to_db(event_type, details):
    global last_event_time

    timestamp = get_local_timestamp()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO mouse_events (timestamp, event_type, details) VALUES (?, ?, ?)',
        (timestamp, event_type, details)
    )
    conn.commit()
    last_id = cursor.lastrowid

    # إنشاء ملف CSV إذا غير موجود وكتابة رأس الأعمدة
    try:
        with open(CSV_FILE, mode="x", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Timestamp", "Event Type", "Details"])
    except FileExistsError:
        pass

    with open(CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([last_id, timestamp, event_type, details])

    print(f"Logged: {last_id}, {timestamp}, {event_type}, {details}")
    conn.close()

    current_event_time = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    if last_event_time:
        delta = (current_event_time - last_event_time).total_seconds()
        if delta > IDLE_THRESHOLD:
            from_time = last_event_time.strftime("%H:%M:%S")
            to_time = current_event_time.strftime("%H:%M:%S")
            duration = f"{delta / 60:.2f}"
            date = last_event_time.date().isoformat()
            save_idle_summary(date, from_time, to_time, duration)
            print(f"Idle period recorded from {from_time} to {to_time}, duration {duration} minutes")
    last_event_time = current_event_time

def log_event(message):
    with open(LOG_FILE, "a") as f:
        timestamp = get_local_timestamp()
        f.write(f"{timestamp}: {message}\n")

def on_move(x, y):
    global last_logged_position, last_logged_move_time
    if stop_flag:
        return

    current_time = datetime.datetime.now()
    if last_logged_move_time is None or (current_time - last_logged_move_time).total_seconds() > LOG_INTERVAL:
        if last_logged_position is None or abs(x - last_logged_position[0]) > MOVE_THRESHOLD or abs(y - last_logged_position[1]) > MOVE_THRESHOLD:
            log_event(f"Move: ({x}, {y})")
            log_to_db("Move", f"Position: ({x}, {y})")
            last_logged_position = (x, y)
            last_logged_move_time = current_time

def on_click(x, y, button, pressed):
    global last_click_time
    if not stop_flag and pressed:
        current_time = datetime.datetime.now()
        if last_click_time is None or (current_time - last_click_time).total_seconds() > CLICK_DEBOUNCE:
            log_event(f"Click: ({x}, {y}) [{button}]")
            log_to_db("Click", f"Position: ({x}, {y}), Button: {button}")
            last_click_time = current_time

def on_scroll(x, y, dx, dy):
    if not stop_flag and (abs(dx) > SCROLL_THRESHOLD or abs(dy) > SCROLL_THRESHOLD):
        log_event(f"Scroll: ({x}, {y}) Delta: ({dx}, {dy})")
        log_to_db("Scroll", f"Position: ({x}, {y}), Delta: ({dx}, {dy})")

def on_press(key):
    global stop_flag
    stop_flag = True
    log_event("Key pressed. Stopping tracking.")
    log_to_db("Key Press", "Stopping tracking")
    return False

def analyze_idle_time(input_csv, output_csv, idle_threshold=IDLE_THRESHOLD):
    last_timestamp = None
    rows_with_idle = []

    with open(input_csv, mode="r") as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames + ["Idle Time (Minutes)"]
        for row in reader:
            try:
                current_timestamp = datetime.datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                current_timestamp = datetime.datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")

            idle_time = ""
            if last_timestamp:
                time_diff = (current_timestamp - last_timestamp).total_seconds()
                if time_diff > idle_threshold:
                    idle_time = f"{time_diff / 60:.2f} minutes"
            last_timestamp = current_timestamp
            row["Idle Time (Minutes)"] = idle_time
            rows_with_idle.append(row)

    with open(output_csv, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_with_idle)

    print(f"✅ Idle time analysis saved to {output_csv}")

def summarize_idle_by_day(input_csv, summary_csv, idle_threshold=IDLE_THRESHOLD):
    idle_periods_by_day = defaultdict(list)
    last_time = None

    with open(input_csv, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                current_time = datetime.datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                current_time = datetime.datetime.strptime(row["Timestamp"], "%Y-%m-%d %H:%M:%S")

            if last_time:
                delta = (current_time - last_time).total_seconds()
                if delta >= idle_threshold:
                    date_key = last_time.date().isoformat()
                    idle_periods_by_day[date_key].append({
                        "From": last_time.strftime("%H:%M:%S"),
                        "To": current_time.strftime("%H:%M:%S"),
                        "Duration (Minutes)": f"{delta / 60:.2f}"
                    })
            last_time = current_time

    with open(summary_csv, "w", newline="") as file:
        fieldnames = ["Date", "From", "To", "Duration (Minutes)"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for date, periods in idle_periods_by_day.items():
            for period in periods:
                writer.writerow({
                    "Date": date,
                    **period
                })

    print(f"📊 Daily idle summary saved to: {summary_csv}")

def main():
    global stop_flag, last_event_time
    init_db()
    print("🟢 Mouse tracking started. Press any key to stop.", flush=True)

    with keyboard.Listener(on_press=on_press) as keyboard_listener:
        with mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll) as mouse_listener:
            while not stop_flag:
                pass

    # Log any remaining idle period when stopping
    if last_event_time:
        now = datetime.datetime.now()
        delta = (now - last_event_time).total_seconds()
        if delta > IDLE_THRESHOLD:
            from_time = last_event_time.strftime("%H:%M:%S")
            to_time = now.strftime("%H:%M:%S")
            duration = f"{delta / 60:.2f}"
            date = last_event_time.date().isoformat()
            save_idle_summary(date, from_time, to_time, duration)
            print(f"📥 Final idle period saved from {from_time} to {to_time}")

    analyze_idle_time(CSV_FILE, OUTPUT_CSV_FILE)
    summarize_idle_by_day(CSV_FILE, SUMMARY_CSV_FILE)

if __name__ == "__main__":
    main()
