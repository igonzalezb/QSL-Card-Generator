# ==============================================================================
# QSL Card Generator
# Copyright (C) 2026 LU2EXV (igonzalezb)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# ==============================================================================
import sys
import logging
from logging.handlers import RotatingFileHandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from core.utils import resource_path
from core.utils import LOG_FILE
from ui.main_window import QSLGeneratorApp

file_handler = RotatingFileHandler(
    LOG_FILE, 
    maxBytes=1 * 1024 * 1024,
    backupCount=1,           
    encoding='utf-8'
)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler]
)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    app.setWindowIcon(QIcon(resource_path("icon.svg")))
    
    try:
        window = QSLGeneratorApp()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        logging.critical(f"Error: {e}", exc_info=True)