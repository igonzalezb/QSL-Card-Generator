import sys
import os

def resource_path(relative_path):
    """ Gets the absolute path of the resources, compatible with PyInstaller (_MEIPASS) """
    try:
        # PyInstaller creates a temporary folder and saves the path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)