import os
import logging
import concurrent.futures
from PyQt6.QtCore import QThread, pyqtSignal
from PIL import Image
from core.engine import draw_qsl_core

logger = logging.getLogger(__name__)

class ExportWorker(QThread):
    progress = pyqtSignal(int)
    finished_export = pyqtSignal(int, list, bool)
    
    def __init__(self, bg_path: str, config: dict, export_data: list, out_dir: str):
        super().__init__()
        self.bg_path = bg_path
        self.config = config
        self.export_data = export_data
        self.out_dir = out_dir
        self.num_threads = config.get("threads", 1)
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
        
    def process_single_qsl(self, item, base_img_path):
        """Función interna que procesa una sola tarjeta"""
        if self._is_cancelled:
            return None
        
        try:
            with Image.open(base_img_path).convert("RGBA") as base_img:
                final_img, call = draw_qsl_core(base_img, self.config, item['data'])
                base_filename = f"{item['row']}_QSL_{call.replace('/', '-')}"
                save_path = os.path.join(self.out_dir, f"{base_filename}.png")
                
                counter = 1
                while os.path.exists(save_path):
                    save_path = os.path.join(self.out_dir, f"{base_filename}({counter}).png")
                    counter += 1
                
                final_img.save(save_path, "PNG")
                return True
        except Exception as e:
            return f"Fila {item['row'] + 1}: {str(e)}"

    def run(self):
        logger.info(f"Iniciando exportación de {len(self.export_data)} QSLs con {self.num_threads} hilos.")
        processed = 0
        errors = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = [executor.submit(self.process_single_qsl, item, self.bg_path) for item in self.export_data]
            
            for future in concurrent.futures.as_completed(futures):
                if self._is_cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                
                result = future.result()
                if result is True:
                    processed += 1
                elif result is not None:
                    errors.append(result)
                
                self.progress.emit(processed + len(errors))

        self.finished_export.emit(processed, errors, self._is_cancelled)