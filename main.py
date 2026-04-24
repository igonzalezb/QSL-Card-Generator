import sys
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from core.utils import resource_path

logging.basicConfig(
    filename='qsl_info.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from ui.main_window import QSLGeneratorApp

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