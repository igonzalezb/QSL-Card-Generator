from PyQt6.QtWidgets import (QDialog, QFormLayout, QComboBox, QLineEdit, 
                             QHBoxLayout, QPushButton, QFileDialog, QSpinBox, 
                             QColorDialog, QDialogButtonBox, QCheckBox, 
                             QSlider, QLabel, QGridLayout)
from PyQt6.QtCore import Qt 
from PyQt6.QtGui import QColor
from core.i18n import tr, CURRENT_LANG
import os

class SettingsDialog(QDialog):
    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("set_title"))
        self.resize(400, 350)
        self.config = config.copy()
        layout = QFormLayout(self)
        
        self.cmb_lang = QComboBox()
        self.cmb_lang.addItem(tr("lang_sys"), "default")
        self.cmb_lang.addItem("Español", "es")
        self.cmb_lang.addItem("English", "en")
        idx = self.cmb_lang.findData(self.config.get("lang", "default"))
        if idx >= 0: self.cmb_lang.setCurrentIndex(idx)
        
        self.cmb_lang.currentIndexChanged.connect(self.refresh_combo_pos)
        layout.addRow(tr("set_lang"), self.cmb_lang)
        
        self.inp_call = QLineEdit(self.config.get("callsign", ""))
        layout.addRow(tr("set_call"), self.inp_call)
        
        bg_lay = QHBoxLayout()
        self.inp_bg = QLineEdit(self.config.get("default_bg", ""))
        btn_br = QPushButton(tr("btn_browse"))
        btn_br.clicked.connect(self.browse_bg)
        bg_lay.addWidget(self.inp_bg)
        bg_lay.addWidget(btn_br)
        layout.addRow(tr("set_def_bg"), bg_lay)
               
        self.cmb_pos = QComboBox()
        self.refresh_combo_pos()
        layout.addRow(tr("set_pos"), self.cmb_pos)
        
        scale_lay = QHBoxLayout()
        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setMinimum(2)
        self.slider_scale.setMaximum(50)
        
        initial_scale = self.config.get("table_scale", 1.0)
        self.slider_scale.setValue(int(initial_scale * 10))
        
        self.lbl_scale_val = QLabel(f"x {initial_scale:.1f}")
        self.lbl_scale_val.setMinimumWidth(40)
        
        self.slider_scale.valueChanged.connect(
            lambda val: self.lbl_scale_val.setText(f"x {val / 10.0:.1f}")
        )
        
        scale_lay.addWidget(self.slider_scale)
        scale_lay.addWidget(self.lbl_scale_val)
        layout.addRow(tr("set_scale"), scale_lay)
        
        self.spn_opac = QSpinBox()
        self.spn_opac.setMaximum(100)
        self.spn_opac.setValue(self.config.get("opacity", 85))
        layout.addRow(tr("set_opac"), self.spn_opac)
        
        self.spin_threads = QSpinBox()
        cores = os.cpu_count() or 1
        self.spin_threads.setRange(1, cores)
        self.spin_threads.setValue(self.config.get("threads", 1))
        layout.addRow(tr("set_threads"), self.spin_threads)
        
        lang = self.config.get("lang", "default")
        if lang == "default":
            lang = CURRENT_LANG
            
        if lang == "es":
            txt_headers = "Títulos:"
            txt_data = "Contactos:"
            txt_bg = "Fondo"
            txt_txt = "Texto"
        else:
            txt_headers = "Headers:"
            txt_data = "Data:"
            txt_bg = "Background"
            txt_txt = "Text"
        
        color_grid = QGridLayout()
        color_grid.setContentsMargins(0, 0, 0, 0)
        
        btn_h_bg = QPushButton(txt_bg)
        btn_h_txt = QPushButton(txt_txt)
        btn_d_bg = QPushButton(txt_bg)
        btn_d_txt = QPushButton(txt_txt)
        
        color_grid.addWidget(QLabel(txt_headers), 0, 0)
        color_grid.addWidget(btn_h_bg, 0, 1)
        color_grid.addWidget(btn_h_txt, 0, 2)
        
        color_grid.addWidget(QLabel(txt_data), 1, 0)
        color_grid.addWidget(btn_d_bg, 1, 1)
        color_grid.addWidget(btn_d_txt, 1, 2)
        
        for btn, key in [(btn_h_bg, "color_h_bg"), (btn_h_txt, "color_h_txt"), 
                         (btn_d_bg, "color_d_bg"), (btn_d_txt, "color_d_txt")]:
            self.update_btn_color(btn, self.config[key])
            btn.clicked.connect(lambda chk, b=btn, k=key: self.pick_color(k, b))
            
        layout.addRow(tr("set_color"), color_grid)
        
        self.chk_comments = QCheckBox()
        self.chk_comments.setChecked(self.config.get("show_comments", True))
        
        lbl_comments = QLabel(tr("set_comments"))
        lbl_comments.setWordWrap(True)
        
        layout.addRow(lbl_comments, self.chk_comments)
                
        self.bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.bb.accepted.connect(self.accept); self.bb.rejected.connect(self.reject)
        layout.addWidget(self.bb)
        self.adjustSize()

    def refresh_combo_pos(self):
        lang = self.cmb_lang.currentData()
        if lang == "default": lang = CURRENT_LANG
        current_selection = self.cmb_pos.currentData() or self.config.get("pos", "bottom_center")
            
        self.cmb_pos.clear()
        opts = tr("pos_options")
        if isinstance(opts, dict):
            for key, text in opts.items():
                self.cmb_pos.addItem(text, key)
            
        idx = self.cmb_pos.findData(current_selection)
        if idx >= 0: self.cmb_pos.setCurrentIndex(idx)

    def browse_bg(self):
        fn, _ = QFileDialog.getOpenFileName(self, tr("btn_browse"), "", "Images (*.png *.jpg *.jpeg)")
        if fn: self.inp_bg.setText(fn)

    def pick_color(self, k: str, b: QPushButton):
        c = QColorDialog.getColor(QColor(self.config[k]), self, "Color")
        if c.isValid(): 
            self.config[k] = c.name()
            self.update_btn_color(b, c.name())

    def update_btn_color(self, b: QPushButton, hex_c: str):
        c = QColor(hex_c)
        tc = "black" if (c.red()*0.299 + c.green()*0.587 + c.blue()*0.114) > 186 else "white"
        b.setStyleSheet(f"background-color: {hex_c}; color: {tc}; border: 1px solid #aaa; border-radius: 4px; padding: 4px;")

    def get_data(self) -> dict:
        self.config.update({
            "lang": self.cmb_lang.currentData(),
            "threads": self.spin_threads.value(), 
            "callsign": self.inp_call.text().strip().upper(), 
            "default_bg": self.inp_bg.text().strip(), 
            "pos": self.cmb_pos.currentData(), 
            "opacity": self.spn_opac.value(),
            "table_scale": self.slider_scale.value() / 10.0, 
            "show_comments": self.chk_comments.isChecked()
        })
        return self.config