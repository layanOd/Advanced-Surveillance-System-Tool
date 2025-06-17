import win32com.client
import csv
import os
from datetime import datetime, timedelta
from transformers import pipeline
import sys
import io

# Set UTF-8 encoding for standard output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# === Constants ===
CSV_FILE = "email_export.csv"
TIMESTAMP_LOG = "email_log_times.txt"

# === Load AI Model ===
model = pipeline("text-classification", model="./behavior_model")
label_map = {
    "LABEL_0": "inappropriate",
    "LABEL_1": "normal",
    "LABEL_2": "normal"
}

# === Ensure CSV File Has Header ===
def ensure_csv_header():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=["Sender", "Subject", "Received Time", "Body Preview", "Label"])
            writer.writeheader()

# === Load Previously Saved Email Timestamps ===
def load_saved_times():
    if os.path.exists(TIMESTAMP_LOG):
        with open(TIMESTAMP_LOG, 'r', encoding='utf-8') as file:
            return set(file.read().splitlines())
    return set()

# === Save New Timestamps to Log ===
def save_new_times(times):
    with open(TIMESTAMP_LOG, 'a', encoding='utf-8') as file:
        for t in times:
            file.write(t + '\n')

# === Classify Text with AI ===
def classify_text(text):
    try:
        result = model(text)
        label = result[0]["label"]
        return label_map.get(label, "unknown")
    except Exception as e:
        print(f"⚠️ AI classification error: {e}", flush=True)
        return "error"

# === Extract Emails from Outlook ===
def extract_emails():
    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    inbox = outlook.GetDefaultFolder(6)
    sent_items = outlook.GetDefaultFolder(5)

    inbox_messages = inbox.Items
    sent_messages = sent_items.Items

    inbox_messages.Sort("[ReceivedTime]", False)
    sent_messages.Sort("[SentOn]", False)

    # Map of sent emails by ConversationID
    sent_conversations = {}
    for msg in sent_messages:
        try:
            if msg.ConversationID:
                sent_conversations[msg.ConversationID] = msg
        except:
            continue

    saved_times = load_saved_times()
    output_data = []
    new_times = []

    for msg in inbox_messages:
        try:
            received_time = msg.ReceivedTime
            received_time_str = received_time.strftime('%Y-%m-%d %H:%M')

            if received_time_str in saved_times:
                continue

            body_preview = msg.Body[:200].replace('\n', ' ').replace('\r', ' ')
            label = classify_text(body_preview)

            email_data = {
                "Sender": f"Sender: {msg.SenderName}",
                "Subject": f"Subject: {msg.Subject}",
                "Received Time": f"Received Time: {received_time_str}",
                "Body Preview": f"Body Preview: {body_preview}",
                "Label": label
            }
            output_data.append(email_data)
            new_times.append(received_time_str)

            # Check for reply within 2 days
            conv_id = msg.ConversationID
            if conv_id in sent_conversations:
                reply = sent_conversations[conv_id]
                if reply.SentOn > received_time and (reply.SentOn - received_time) < timedelta(days=2):
                    reply_preview = reply.Body[:200].replace('\n', ' ').replace('\r', ' ')
                    reply_label = classify_text(reply_preview)
                    reply_time_str = reply.SentOn.strftime('%Y-%m-%d %H:%M')

                    reply_data = {
                        "Sender": f"Replied by: {reply.SenderName}",
                        "Subject": f"Re: {reply.Subject}",
                        "Received Time": f"Sent Time: {reply_time_str}",
                        "Body Preview": f"Reply Preview: {reply_preview}",
                        "Label": reply_label
                    }
                    output_data.append(reply_data)
                    new_times.append(reply_time_str)

        except Exception as e:
            print(f"⚠️ Error processing email: {e}", flush=True)
            continue

    return output_data, new_times

# === Save Email Data to CSV ===
def save_to_csv(data):
    with open(CSV_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Sender", "Subject", "Received Time", "Body Preview", "Label"])
        writer.writerows(data)

# === Main Function ===
def main():
    print("📨 Starting Outlook email logger ...", flush=True)
    ensure_csv_header()
    email_data, timestamps = extract_emails()

    if email_data:
        save_to_csv(email_data)
        save_new_times(timestamps)
        print(f"✅ Done. {len(timestamps)} new entries saved to {CSV_FILE}", flush=True)
    else:
        print("⚠️ No new emails to log.", flush=True)

if __name__ == "__main__":
    main()
