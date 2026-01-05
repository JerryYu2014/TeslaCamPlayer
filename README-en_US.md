# TeslaCamPlayer

[![CI Status](https://github.com/JerryYu2014/TeslaCamPlayer/actions/workflows/ci.yml/badge.svg)](https://github.com/JerryYu2014/TeslaCamPlayer/actions/workflows/ci.yml)

TeslaCamPlayer is a desktop player and manager for Tesla dashcam (TeslaCam / Sentry Mode) video files. 
It is built with Python and PyQt5, providing a cross‑platform GUI to quickly browse, preview, and export TeslaCam clips.

> 中文说明：请参见 [README.md](README.md)

---

## Features

- **Browse & play TeslaCam videos**  
  Load loop recording and Sentry Mode footage from TeslaCam USB drives or copied folders, and play clips continuously.
- **Multi‑view playback**  
  Use `python-vlc` and `ffmpeg-python` under the hood to support multiple video streams and timeline control.
- **Clip export & merge**  
  Export selected time ranges to standalone video files, with basic merging capabilities (powered by FFmpeg).
- **Modern desktop UI**  
  PyQt5 + qt-material + QtAwesome provide a Material‑style, modern desktop interface.
- **System notifications**  
  On Windows, `win11toast` is used to display system‑level notifications.

> The actual feature set depends on the released version. See `MainWindow.py` and `TeslaCamPlayerWidget.py` for the main entry points and UI logic.

---

## Tech Stack

- **Language & runtime**  
  - Python 3.9+ (recommended; adjust to your local environment)
- **GUI & UI**  
  - PyQt5 (`PyQt5`)
  - qt-material (`qt-material`)
  - QtAwesome (`QtAwesome`)
- **Media & video processing**  
  - python-vlc (`python-vlc`)
  - ffmpeg-python (`ffmpeg-python`)
- **Utilities & OS integration**  
  - win11toast (Windows notifications)
  - requests (network requests, e.g. for checking updates or downloading resources)
- **Packaging & distribution**  
  - PyInstaller (`pyinstaller`)
  - Windows installer: NSIS
  - macOS installer: Packages (pkg)

See `requirements.txt` for the full list of dependencies.

---

## Project Structure (Simplified)

```text
TeslaCamPlayer/
├─ src/
│  ├─ MainWindow.py              # Main application window
│  ├─ TeslaCamPlayerWidget.py    # Main player / manager UI
│  ├─ CoreWorker.py              # Background tasks and core logic
│  ├─ CamClipCombiner/           # Video clip merger
│  │  ├─ CamClipCombinerWin.py   # Merge dialog UI
│  │  └─ CoreWorker.py           # Core merge logic
│  ├─ ThemeManager.py            # Theme & style management
│  ├─ GlobalConfig.py            # Global configuration
│  ├─ notifier.py                # Notification helpers
│  ├─ utils.py                   # Utility helpers
│  └─ assets/                    # Icons and resources
├─ requirements.txt
├─ TeslaCamPlayer.spec           # PyInstaller spec file
├─ TeslaCamPlayer.nsi            # NSIS script (Windows)
├─ TeslaCamPlayer.pkgproj        # Packages project (macOS)
└─ README.md / README-en_US.md
```

---

## Getting Started (Development)

### 1. Create & activate a virtual environment (recommended)

#### Install virtualenv

```bash
pip3 install virtualenv

py -3 -m pip install virtualenv
```

#### Create a virtual environment

```bash
virtualenv venv

py -3 -m virtualenv venv
```

#### Activate the virtual environment

```bash
# macOS / Linux:
source ./venv/bin/activate

# Windows (CMD or PowerShell):
.\venv\scripts\activate
```

#### Deactivate the virtual environment

```bash
deactivate
```

### 2. Install dependencies

From the project root:

```bash
# Default index
pip install -r requirements.txt

# Aliyun mirror
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Tsinghua mirror
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

# Official index with proxy
pip install -r requirements.txt -i https://pypi.org/simple/ --trusted-host pypi.org --proxy http://127.0.0.1:1081

# Install ffmpeg-python separately if needed
pip install ffmpeg-python
```

#### Uninstall dependencies (optional)

```bash
pip uninstall -r requirements.txt

pip uninstall python-ffmpeg
```

> Note: You must have FFmpeg installed on your system, and the `ffmpeg` binary should be available in your `PATH` for export/merge features to work.

---

## Run from Source

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-name>/TeslaCamPlayer.git
   cd TeslaCamPlayer
   ```

2. (Optional) create & activate a virtual environment, then install dependencies:

   ```bash
   py -3 -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the main application:

   ```bash
   # Windows
   py -3 src/MainWindow.py

   # Other platforms
   python src/MainWindow.py
   ```

4. Insert the USB drive (or choose a local folder) that contains the TeslaCam directory structure, then select the path in the app and start browsing/playing.

---

## Build Executables & Installers

### 1. Build executables with PyInstaller

Make sure PyInstaller is installed (it is listed in `requirements.txt`):

```bash
pip install pyinstaller
```

#### Windows examples

```bash
# One-file mode (slower startup time)
pyinstaller --onefile src/MainWindow.py --noconfirm --name "TeslaCamPlayer"

# GUI app, hide console window
pyinstaller src/MainWindow.py --windowed --noconfirm --name "TeslaCamPlayer"

# Strip debug symbols, reduce size
pyinstaller src/MainWindow.py --windowed --noconfirm --strip --name "TeslaCamPlayer"

# Add icon and resources
pyinstaller src/MainWindow.py --windowed --noconfirm --strip --name "TeslaCamPlayer" \
  --add-data "src/assets/*:assets" --icon="src/assets/logo.ico"

# Use the spec file (recommended for consistent builds)
pyinstaller --noconfirm TeslaCamPlayer.spec
```

#### macOS examples

```bash
# One-file mode
pyinstaller --onefile src/MainWindow.py --noconfirm --name "TeslaCamPlayer"

# GUI app
pyinstaller src/MainWindow.py --windowed --noconfirm --name "TeslaCamPlayer"

# Strip debug symbols
pyinstaller src/MainWindow.py --windowed --noconfirm --strip --name "TeslaCamPlayer"

# Icon and resources
pyinstaller src/MainWindow.py --windowed --noconfirm --strip --name "TeslaCamPlayer" \
  --add-data "src/assets/*:assets" --icon="src/assets/logo.ico"

# Use the spec file
pyinstaller --noconfirm TeslaCamPlayer.spec
```

> Adjust the `--add-data` paths and icon file according to your actual directory layout and platform.

#### GitHub Actions auto-published artifacts

When you push a tag like `v1.0.x` to GitHub, the `C.Build and Release` workflow runs automatically and publishes installable artifacts to the corresponding GitHub Release:

- **Windows**:
  - `TeslaCamPlayer X.Y.Z_Setup.exe` — NSIS installer for Windows.
- **macOS**:
  - `TeslaCamPlayer-macOS-universal.dmg` — a **universal2** DMG that supports both Apple Silicon and Intel Macs.

End users can simply download these files from the Releases page and install the app on their platform.

### 2. Build installers

#### Windows: NSIS installer

- Install [NSIS](https://nsis.sourceforge.io/Main_Page).
- Use the `TeslaCamPlayer.nsi` script in this repository to generate a Windows installer.

#### macOS: pkg installer

- Install [Packages](http://s.sudre.free.fr/Software/Packages/about.html).
- Open the `TeslaCamPlayer.pkgproj` project and build a pkg installer.

---

## License

This project is open-sourced under the [MIT License](LICENSE). Contributions via issues and pull requests are welcome.
