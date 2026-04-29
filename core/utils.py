import sys
import os
from pathlib import Path

HOME_DIR = str(Path.home())
APP_DIR = os.path.join(HOME_DIR, ".qsl_generator")

if not os.path.exists(APP_DIR):
    os.makedirs(APP_DIR)

CONFIG_FILE = os.path.join(APP_DIR, "qsl_config.json")
LOG_FILE = os.path.join(APP_DIR, "qsl.log")

def resource_path(relative_path):
    """ Gets the absolute path of the resources, compatible with PyInstaller (_MEIPASS) """
    try:
        # PyInstaller creates a temporary folder and saves the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)