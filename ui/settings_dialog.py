from PyQt6.QtWidgets import QDialog, QFormLayout, QComboBox, QLineEdit, QHBoxLayout, QPushButton, QFileDialog, QSpinBox, QDoubleSpinBox, QColorDialog, QDialogButtonBox, QCheckBox
from PyQt6.QtGui import QColor
from core.i18n import tr, CURRENT_LANG

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
        
        self.spn_scale = QDoubleSpinBox()
        self.spn_scale.setPrefix("x ")
        self.spn_scale.setMinimum(0.2)
        self.spn_scale.setMaximum(5.0)
        self.spn_scale.setSingleStep(0.1)
        self.spn_scale.setValue(self.config.get("table_scale", 1.0))
        layout.addRow(tr("set_scale"), self.spn_scale)
        
        self.spn_opac = QSpinBox()
        self.spn_opac.setMaximum(100)
        self.spn_opac.setValue(self.config.get("opacity", 85))
        layout.addRow(tr("set_opac"), self.spn_opac)
        
        c_lay = QHBoxLayout()
        for k, label in [("color_h_bg", "H-BG"), ("color_h_txt", "H-TX"), ("color_d_bg", "D-BG"), ("color_d_txt", "D-TX")]:
            b = QPushButton(label); self.update_btn_color(b, self.config[k])
            b.clicked.connect(lambda chk, btn=b, key=k: self.pick_color(key, btn))
            c_lay.addWidget(b)
        layout.addRow(tr("set_color"), c_lay)
        
        self.chk_comments = QCheckBox()
        self.chk_comments.setChecked(self.config.get("show_comments", True))
        layout.addRow(tr("set_comments"), self.chk_comments)
        
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
                "callsign": self.inp_call.text().strip().upper(), 
                "default_bg": self.inp_bg.text().strip(), 
                "pos": self.cmb_pos.currentData(), 
                "opacity": self.spn_opac.value(),
                "table_scale": self.spn_scale.value(),
                "show_comments": self.chk_comments.isChecked()
            })
            return self.config