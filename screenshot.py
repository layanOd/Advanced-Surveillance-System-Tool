import pyautogui
import time
import os
from datetime import datetime

def capture_screenshots():
    output_folder = "screenshots"

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    interval = 10  # every 10 seconds
    num_screenshots = 5  # number of screenshots

    for i in range(num_screenshots):
        try:
            screenshot = pyautogui.screenshot()
            screenshot_path = os.path.join(output_folder, f"screenshot_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            screenshot.save(screenshot_path)
            print(f"Screenshot {i+1} saved at {screenshot_path}")
        except Exception as e:
            print(f"Failed to capture screenshot {i+1}: {e}")
        time.sleep(interval)

    print("Screenshots captured successfully.")

def main():
    capture_screenshots()

if __name__ == "__main__":
    main()