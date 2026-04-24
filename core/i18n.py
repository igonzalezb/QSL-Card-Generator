import json
import os
import logging
from PyQt6.QtCore import QLocale
from core.utils import resource_path

logger = logging.getLogger(__name__)

CURRENT_LANG = "en"
_translations = {}

def init_i18n(lang_code: str = "default") -> None:
    global CURRENT_LANG, _translations
    if lang_code == "default":
        sys_l = QLocale.system().name()[:2]
        CURRENT_LANG = sys_l if sys_l in ["es", "en"] else "en"
    else:
        CURRENT_LANG = lang_code
        
    path = resource_path(os.path.join("locales", f"{CURRENT_LANG}.json"))
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            _translations = json.load(f)
    except Exception as e:
        logger.error(f"Error loading language: {e}")
        _translations = {}

def tr(key: str) -> any:
    return _translations.get(key, key)