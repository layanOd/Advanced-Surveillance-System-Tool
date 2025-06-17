# main.py
import os
import sys
import csv
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit,
    QMainWindow, QTabWidget, QSplashScreen, QFileDialog, QMessageBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QTimer, QProcess

os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"


class ScriptTab(QWidget):
    def __init__(self, script_name):
        super().__init__()
        layout = QVBoxLayout()
        self.script_name = script_name
        self.process = None
        self.selected_folder = None

        self.run_button = QPushButton(f"Run {script_name}")
        self.run_button.setStyleSheet(self.button_style("#00FF7F"))
        self.run_button.clicked.connect(self.run_script)

        self.stop_button = QPushButton(f"Stop {script_name}")
        self.stop_button.setStyleSheet(self.button_style("#FF6347"))
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)

        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                border: 1px solid #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #FFFFFF;
            }
        """)

        layout.addWidget(self.run_button)
        layout.addWidget(self.stop_button)

        if script_name == "cwd":
            self.browse_button = QPushButton("Browse Directory")
            self.browse_button.setStyleSheet(self.run_button.styleSheet())
            self.browse_button.clicked.connect(self.browse_folder)
            layout.addWidget(self.browse_button)

        layout.addWidget(self.output_area)
        self.setLayout(layout)

    def button_style(self, color):
        return f"""
            QPushButton {{
                background-color: #1E1E1E;
                color: {color};
                border: 2px solid {color};
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2E2E2E;
            }}
        """

    def browse_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.selected_folder = folder_path
            self.output_area.append(f"Selected folder: {folder_path}")

    def run_script(self):
        if self.process is None:
            self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.process_finished)

        try:
            # Determine the Python interpreter to use
            if getattr(sys, 'frozen', False):  # If running as a PyInstaller .exe
                python_executable = "python"  # Use the system-wide Python interpreter
            else:  # If running as a regular Python script
                python_executable = sys.executable

            # Locate the script path
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(base_dir, f"{self.script_name}.py")

            # Verify that the script exists
            if not os.path.exists(script_path):
                self.output_area.append(f"Error: Script not found: {script_path}")
                return

            # Prepare the arguments
            args = [python_executable, script_path]

            # Add additional arguments for specific scripts (e.g., cwd)
            if self.script_name == "cwd":
                args.append(self.selected_folder or os.getcwd())

            # Log the arguments in the output area
            self.output_area.append(f"Running script with arguments: {args}")

            # Start the process
            self.process.start(args[0], args[1:])
            if not self.process.waitForStarted(5000):  # Wait for the process to start (5 seconds)
                self.output_area.append("Error: Failed to start the script.")
                return

            self.run_button.setEnabled(False)
            self.stop_button.setEnabled(True)

        except Exception as e:
            self.output_area.append(f"Error starting script: {e}")

    def read_output(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.output_area.append(data.strip())

    def read_error(self):
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.output_area.append(f"ERROR: {data.strip()}")

    def stop_script(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.output_area.append(f"{self.script_name} stopped.")

    def process_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.output_area.append(f"{self.script_name} finished.")
        self.process = None


class HelpTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setPlainText(
            "Help Information:\n\n"
            "keylogger - Log keystrokes\n"
            "application - Monitor applications\n"
            "cwd - Log files in directory\n"
            "File Viewer - View files\n"
            "pinginfo - Check internet\n"
            "vpn - VPN status\n"
            "clipboard - Clipboard logging\n"
            "mouse - Mouse tracker\n"
            "emails - Email logging\n"
            "screenshot - Capture screen\n"
        )
        help_text.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                border: 1px solid #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #FFFFFF;
            }
        """)

        layout.addWidget(help_text)
        self.setLayout(layout)


class FileViewerTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.browse_button = QPushButton("Browse File")
        self.browse_button.setStyleSheet("""
            QPushButton {
                background-color: #1E1E1E;
                color: #00FF7F;
                border: 2px solid #00FF7F;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2E2E2E;
            }
        """)
        self.browse_button.clicked.connect(self.open_file)
        layout.addWidget(self.browse_button)

        self.file_content_area = QTextEdit()
        self.file_content_area.setReadOnly(True)
        self.file_content_area.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                border: 1px solid #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #FFFFFF;
            }
        """)
        layout.addWidget(self.file_content_area)

        self.setLayout(layout)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*.*);;CSV Files (*.csv);;Executable Files (*.exe)"
        )
        if file_path:
            try:
                # Try reading the file with UTF-8 encoding
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                self.file_content_area.setPlainText(content)
            except UnicodeDecodeError:
                try:
                    # If UTF-8 fails, try reading with a different encoding (e.g., ISO-8859-1)
                    with open(file_path, "r", encoding="ISO-8859-1") as file:
                        content = file.read()
                    self.file_content_area.setPlainText(content)
                except Exception as e:
                    # If all else fails, show an error message
                    self.file_content_area.setPlainText(f"Error reading file: {e}")

class MalwareTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.process = None

        # Run Button
        self.run_button = QPushButton("Run Malware Script")
        self.run_button.setStyleSheet(self.button_style("#00FF7F"))
        self.run_button.clicked.connect(self.run_script)

        # Stop Button
        self.stop_button = QPushButton("Stop Malware Script")
        self.stop_button.setStyleSheet(self.button_style("#FF6347"))
        self.stop_button.clicked.connect(self.stop_script)
        self.stop_button.setEnabled(False)

        # Check for Malware Button
        self.check_button = QPushButton("Check for Malware")
        self.check_button.setStyleSheet(self.button_style("#FFD700"))
        self.check_button.clicked.connect(self.check_for_malware)

        # Output Area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #121212;
                border: 1px solid #333333;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
                color: #FFFFFF;
            }
        """)

        # Add widgets to layout
        layout.addWidget(self.run_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.check_button)
        layout.addWidget(self.output_area)
        self.setLayout(layout)

    def button_style(self, color):
        return f"""
            QPushButton {{
                background-color: #1E1E1E;
                color: {color};
                border: 2px solid {color};
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #2E2E2E;
            }}
        """

    def run_script(self):
        if self.process is None:
            self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_error)
        self.process.finished.connect(self.process_finished)

        # Use the Python interpreter explicitly
        if getattr(sys, 'frozen', False):
            # If bundled with PyInstaller, use system Python to run malware.py
            python_executable = "python"  # Or full path to python.exe if needed
            script_path = os.path.join(sys._MEIPASS, "malware.py")
        else:
            # Normal dev mode
            python_executable = sys.executable
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "malware.py")

        args = [python_executable, script_path]

        self.output_area.append(f"Running script with arguments: {args}")
        self.process.start(args[0], args[1:])  # Start the process with the Python interpreter

        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_script(self):
        if self.process:
            self.process.terminate()
            self.process = None
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.output_area.append("Malware script stopped.")

    def check_for_malware(self):
        # Open a file dialog to select a CSV file
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        if file_path:
            self.output_area.append(f"Selected CSV file: {file_path}")
            # Process the selected CSV file (placeholder logic)
            self.process_csv(file_path)

    def process_csv(self, file_path):
        try:
            with open(file_path, mode='r', encoding='utf-8') as file:
                reader = csv.reader(file)
                self.output_area.append("Processing CSV file...")
                for row in reader:
                    self.output_area.append(f"Row: {row}")
                self.output_area.append("CSV file processed successfully.")
        except Exception as e:
            self.output_area.append(f"Error processing CSV file: {e}")

    def read_output(self):
        if self.process:
            data = self.process.readAllStandardOutput().data().decode()
            self.output_area.append(data.strip())

    def read_error(self):
        if self.process:
            data = self.process.readAllStandardError().data().decode()
            self.output_area.append(f"ERROR: {data.strip()}")

    def process_finished(self):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.output_area.append("Malware script finished.")
        self.process = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Surveillance Tool")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #333333;
                background: #121212;
            }
            QTabBar::tab {
                background: #1E1E1E;
                padding: 15px;
                font-size: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #FFFFFF;
                border: 1px solid #333333;
                border-radius: 5px;
                min-width: 150px;
            }
            QTabBar::tab:selected {
                background: #2E2E2E;
                color: #00FF7F;
                font-weight: bold;
            }
        """)
        self.setCentralWidget(self.tabs)

        # Reordered list of scripts to match the desired tab order
        script_names = [
            "keylogger",
            "clipboard",
            "cwd",
            "malware",
            "emails",
            "application",
            "trackingmouse",
            "pinginfo",
            "vpnconnection",
            "screenshot"
        ]

        # Add a tab for each script
        for name in script_names:
            if name == "malware":
                self.tabs.addTab(MalwareTab(), "Malware")
            elif name == "cwd":
                self.tabs.addTab(ScriptTab(name), "CWD")
            else:
                self.tabs.addTab(ScriptTab(name), name.capitalize())

        # Insert the File Viewer tab immediately after the Malware tab
        self.tabs.insertTab(4, FileViewerTab(), "File Viewer")

        # Add the Help menu
        self.create_help_menu()

    def create_help_menu(self):
        # Create a menu bar
        menu_bar = self.menuBar()
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #1E1E1E;
                color: #FFFFFF;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
            }
            QMenuBar::item {
                background-color: #1E1E1E;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #2E2E2E;
            }
        """)

        # Add a Help menu
        help_menu = menu_bar.addMenu("Help")

        # Add "?" option
        help_action = help_menu.addAction("?")
        help_action.triggered.connect(self.show_help)

        # Add "Check for Updates" option
        update_action = help_menu.addAction("Check for Updates")
        update_action.triggered.connect(self.check_for_updates)

    def show_help(self):
        # Show a window with help information
        help_text = (
            "Help Information:\n\n"
            "keylogger - Log keystrokes\n"
            "clipboard - Clipboard logging\n"
            "cwd - Log files in directory\n"
            "malware - Run malware detection\n"
            "File Viewer - View files\n"
            "emails - Email logging\n"
            "application - Monitor applications\n"
            "mouse - Mouse tracker\n"
            "ping - Check internet\n"
            "vpn - VPN status\n"
            "screenshot - Capture screen\n"
        )
        QMessageBox.information(self, "Help", help_text)

    def check_for_updates(self):
        # Show a window indicating the application is up to date
        QMessageBox.information(self, "Check for Updates", "You are up to date!")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Confirmation",
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()  # Allow the window to close
        else:
            event.ignore()  # Prevent the window from closing


def main():
    app = QApplication(sys.argv)

    splash_pix = QPixmap(400, 300)
    splash_pix.fill(Qt.white)

    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setStyleSheet("""
        QSplashScreen {
            background-color: #121212;
            color: #00FF7F;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 24px;
            font-weight: bold;
            border-radius: 10px;
        }
    """)

    messages = [
        "🚀 Welcome to Surveillance Tool...\n ",
        "🛠️ Preparing your tools...\n ",
        "📊 Initializing dashboard...\n ",
        "🔒 Securing your data...\n "
    ]
    current_message_index = 0

    def update_message():
        nonlocal current_message_index
        splash.showMessage(
            messages[current_message_index],
            Qt.AlignCenter | Qt.AlignBottom,
            Qt.black
        )
        current_message_index = (current_message_index + 1) % len(messages)

    timer = QTimer()
    timer.timeout.connect(update_message)
    timer.start(700)

    splash.show()
    QTimer.singleShot(5000, lambda: (timer.stop(), splash.close()))

    window = MainWindow()
    QTimer.singleShot(5000, window.show)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()