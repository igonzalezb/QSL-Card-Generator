import json
import logging
import urllib.request
import ssl  # <-- ¡Faltaba importar ssl!
import certifi
from PyQt6.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)

class UpdateChecker(QThread):
    update_available = pyqtSignal(str, str)

    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version
        self.api_url = "https://api.github.com/repos/igonzalezb/QSL-Card-Generator/releases/latest"

    def run(self):
        try:
            logger.info("Checking for updates on GitHub...")
            req = urllib.request.Request(self.api_url, headers={'User-Agent': 'QSL-Generator-App'})
            
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            

            with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                latest_version = data.get('tag_name', '').lstrip('v')
                release_url = data.get('html_url', '')

                if self.is_newer(self.current_version, latest_version):
                    logger.info(f"New version found!: {latest_version}")
                    self.update_available.emit(latest_version, release_url)
                else:
                    logger.info("The application is up to date.")
        except Exception as e:
            logger.warning(f"Could not check for updates: {e}")

    def is_newer(self, current, latest):
        try:
            cur = tuple(map(int, current.split('.')))
            lat = tuple(map(int, latest.split('.')))
            return lat > cur
        except Exception:
            return current != latest