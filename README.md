<h1 align="center" style="margin-bottom: -8px;">
  <img src="icon.svg" alt="icon" width="90" height="90"><br>
  QSL Card Generator
</h1>

<p align="center" style="margin-top: 0;">
  by LU2EXV
</p>

<p align="center"> 
<img src="https://img.shields.io/badge/platforms-Linux%20%7C%20Windows-blue" alt="Platform">
<img src="https://img.shields.io/github/v/release/igonzalezb/QSL-Card-Generator?label=version&color=green" alt="Latest Release">
</p>

A desktop application for amateur radio operators designed to generate QSL cards in bulk from ADIF log files. Built with Python, PyQt6, and Pillow.

![Screenshot](docs/main_window.png)

## Download

Prebuilt executables for Windows, Linux are available in the latest [GitHub Releases](https://github.com/igonzalezb/QSL-Card-Generator/releases/latest)

## Features

* **ADIF Import:** Load contacts directly from your favorite logging software.
* **Live Preview:** See your QSL card updates in real time.
* **Highly Customizable:**

  * Change table background and text colors.
  * Adjust transparency for seamless blending with the background image.
  * Choose from 7 predefined table positions (top, bottom, left, right, center, etc.).
* **Manual Editing:** Edit contact data directly in the table, add new QSOs manually, or remove unwanted entries.
* **Fast Batch Export:** Uses multithreaded background processing (`QThread`) to export hundreds of QSL cards quickly without freezing the UI.
* **Multilingual:** Built-in support for English and Spanish, with automatic system language detection.
* **Settings Persistence:** Saves your callsign, colors, and preferences for future sessions.

## Project Structure

```text
QSL-Card-Generator/
├── main.py                 # Application entry point
├── qsl_design.ui           # Qt Designer UI file
├── requirements.txt        # Project dependencies
├── core/                   # Core logic
│   ├── engine.py           # Image rendering engine (Pillow)
│   ├── exporter.py         # Background processing threads
│   └── i18n.py             # Internationalization system
│   └── version.py          # Version information
│   └── updater.py          # Update system
│   └── utils.py            # Utility functions
├── ui/                     # UI controllers
│   ├── main_window.py      # Main window
│   └── settings_dialog.py  # Settings dialog
├── locales/                # Language files
│    ├── en.json
│    └── es.json
└── dist/                    # Build scripts and output
    ├── build_windows.py     # Windows build script
    └── build_appimage.py      # Linux build script
```

## Build Executable

### Windows

To create a standalone executable using PyInstaller:

```bash
pip install pyinstaller
python3 ./dist/build_windows.py
```

### Linux

To create AppImage for Linux:

```bash
./dist/build_appimage.sh
```

## Debug Docs

To run the Jekyll server for documentation development (from the `docs/` directory):

```bash
sudo apt-get install ruby-full build-essential zlib1g-dev # Install Ruby and dependencies
gem install jekyll bundler # Install Jekyll and Bundler
bundle config set --local path 'vendor/bundle' # Configure Bundler to install gems locally
bundle install # Install Jekyll dependencies
bundle exec jekyll serve # Start the Jekyll server
```

## Disclaimer

This is a personal project developed for the amateur radio community.  
Feedback, suggestions, and contributions are always welcome!

---

**73 and good DX!**
