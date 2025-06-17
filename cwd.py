#!/usr/bin/env python3.7
import os
import csv
import sys
import re

# Force UTF-8 encoding for the console
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

def extract_info(path='.'):
    output_csv = "files.csv"  # Name of the output CSV file
    cwd_files = []

    # Ensure the CSV file has a header
    with open(output_csv, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Hash"])  # Add header for the CSV file

    # Walk through the directory and collect file information
    for root, dirs, files in os.walk(path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            try:
                # Check if the file name is a hash-like string (e.g., 64-character hexadecimal)
                if re.fullmatch(r"[a-fA-F0-9]{64}", os.path.splitext(file_name)[0]):
                    sanitized_name = os.path.splitext(file_name)[0]  # Remove the extension for hash-like files
                else:
                    sanitized_name = file_name  # Keep the file name with its extension

                cwd_files.append({"hash": sanitized_name})

                # Write the sanitized name to the CSV
                with open(output_csv, mode="a", newline="", encoding="utf-8") as file:
                    writer = csv.writer(file)
                    writer.writerow([sanitized_name])

            except Exception as e:
                print(f"Error processing file {file_path}: {e}", flush=True)
                continue

    print(f"File information saved to {output_csv}")
    return cwd_files


def main():
    # Handle directory path (first argument)
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if not os.path.exists(path):
            print(f"Error: The path '{path}' does not exist.", flush=True)
            sys.exit(1)
    else:
        path = '.'  # Default to current directory

    try:
        info = extract_info(path)
        print(*info, sep="\n", flush=True)
    except Exception as e:
        print(f"Error processing path '{path}': {e}", flush=True)


if __name__ == "__main__":
    main() #calling main function to start the script
