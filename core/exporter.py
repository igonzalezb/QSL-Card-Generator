import os
import logging
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
from core.engine import draw_qsl_core

logger = logging.getLogger(__name__)

class ExportWorker(QThread):
    progress = pyqtSignal(int)
    finished_export = pyqtSignal(int, list)
    
    def __init__(self, bg_path: str, config: dict, export_data: list, out_dir: str):
        super().__init__()
        self.bg_path = bg_path
        self.config = config
        self.export_data = export_data
        self.out_dir = out_dir
        
    def run(self):
        logger.info(f"Starting export of {len(self.export_data)} QSLs.")
        procesados, errores = 0, []
        try:
            base_img = Image.open(self.bg_path).convert("RGBA")
            for i, item in enumerate(self.export_data):
                try:
                    final_img, call = draw_qsl_core(base_img.copy(), self.config, item['data'])
                    save_path = os.path.join(self.out_dir, f"QSL_{call.replace('/', '-')}_{item['row']}.jpg")
                    final_img.save(save_path, "JPEG", quality=100)
                    procesados += 1
                except Exception as e:
                    logger.error(f"Error processing row {item['row']}: {e}")
                    errores.append(f"Row {item['row'] + 1}: {str(e)}")
                self.progress.emit(i + 1)
        except Exception as e: 
            logger.critical(f"Critical error opening base image: {e}")
            errores.append(f"Fatal: {str(e)}")
            
        self.finished_export.emit(procesados, errores)