from pynput.keyboard import Listener
from pyperclip import paste
from transformers import pipeline
from datetime import datetime
from time import sleep
import threading
import csv
import logging
import os

# === AI Model Setup ===
model = pipeline("text-classification", model="./behavior_model")

label_map = {
    "LABEL_0": "inappropriate",
    "LABEL_1": "normal",
    "LABEL_2": "normal"
}

CSV_FILE = "clipboard_log.csv"
next_id = 1  # Global counter for row IDs

# === Ensure CSV File Has Header ===
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Timestamp", "Content", "Label"])  # CSV header

# === Analyze Clipboard Content and Save to CSV ===
def analyze_and_log_clipboard(content):
    global next_id
    if not content.strip():
        return  # Skip empty or whitespace-only content

    try:
        result = model(content)
        label = result[0]["label"]
        score = result[0]["score"]
        readable_label = label_map.get(label, "unknown")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\nClipboard content: {content}", flush=True)
        print(f"Detected as: {readable_label} with score: {score:.2f}", flush=True)

        # Open the CSV file with utf-8 encoding
        with open(CSV_FILE, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow([next_id, timestamp, content, readable_label])
            next_id += 1

    except Exception as e:
        print(f"Error analyzing clipboard content: {e}", flush=True)

# === Key Logger Setup (optional but retained) ===
clipboard_logger = logging.getLogger("clipboard_logger")
clipboard_logger.setLevel(logging.INFO)

if not clipboard_logger.handlers:
    file_handler = logging.FileHandler("Keyclip.Log")
    formatter = logging.Formatter('%(asctime)s:%(message)s')
    file_handler.setFormatter(formatter)
    clipboard_logger.addHandler(file_handler)

def onPress(key):
    clipboard_logger.info('Key: ' + str(key))

def keyLogger(stop_event):
    with Listener(on_press=onPress) as l:
        while not stop_event.is_set():
            l.join(0.1)

# === Clipboard Monitoring Thread ===
def clipLogger(stop_event):
    prev_clip = ""
    while not stop_event.is_set():
        try:
            clip = paste()
            if clip != prev_clip:
                analyze_and_log_clipboard(clip)
                prev_clip = clip
        except Exception as e:
            print(f"Error in clipboard logger: {e}", flush=True)
        sleep(0.2)

# === Main Function ===
def main():
    print("Starting clipboard logger with AI analysis...", flush=True)

    stop_event = threading.Event()
    clip_thread = threading.Thread(target=clipLogger, args=(stop_event,))
    clip_thread.start()

    try:
        while clip_thread.is_alive():
            clip_thread.join(1)
    except KeyboardInterrupt:
        print("\nStopping clipboard logger...", flush=True)
        stop_event.set()
        clip_thread.join()

if __name__ == "__main__":
    main()
