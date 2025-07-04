# Advanced Surveillance System Tool

> This project tracks employee activity using various monitoring tools.

## Features

- Keylogger - Logs Keystrokes
- clipboard - Clipboard logging
- CWD - Log files in diresctory
- malware - Run malware detection
- File Viewer - View files
- Emails - Email logging
- Application - Monitor applications
- Mouse - Mouse tracker
- ping - Checks internet connection
- VPN - VPN status
- Screenshot - Captures screen

## 🔧 Packaging into EXE

To build the executable:

```bash
pip install pyinstaller

pyinstaller --noconfirm --windowed --onefile --add-data "cwd.py;." --add-data "malware.py;." --add-data "keylogger.py;." --add-data "clipboard.py;." --add-data "emails.py;." --add-data "Application.py;." --add-data "trackingmouse.py;." --add-data "pinginfo.py;." --add-data "vpnconnection.py;." --add-data "screenshot.py;." gui.py
```
> This will create a .exe progarm make sure it's in the same path as the scripts and AI model folder 

Or you could just run in terminal
```bash
python gui.py
```
## Configuration

No special config required. Just ensure internet access for malware API.

## Examples
<html>
<video width="600" controls>
  <source src="/my-docs/final_project.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
</html>

## Known Issues

- Malware API may not detect hashes if the sample is not in the public database.
- Some antivirus software may flag the EXE as suspicious due to keylogging features.

## Contributing
Feel free to fork and submit pull requests!

## License
MIT License
