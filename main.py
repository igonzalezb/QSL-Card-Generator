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