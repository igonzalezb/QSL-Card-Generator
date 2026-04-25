import os
import json
import datetime
import logging

from PyQt6.QtWidgets import (
    QMainWindow,
    QFileDialog,
    QTableWidgetItem,
    QMessageBox,
    QProgressDialog,
    QAbstractItemView,
    QScrollArea,
    QMenu,
)
from PyQt6.QtGui import QImage, QPixmap, QDesktopServices
from PyQt6 import uic
from PyQt6.QtCore import Qt, QEvent, QUrl

from PIL import Image, ImageOps
import adif_io

from core.i18n import tr, init_i18n
from core.engine import draw_qsl_core
from core.exporter import ExportWorker
from ui.settings_dialog import SettingsDialog
from core.version import APP_VERSION
from core.updater import UpdateChecker
from core.utils import resource_path

CONFIG_FILE = "qsl_config.json"

logger = logging.getLogger(__name__)


class QSLGeneratorApp(QMainWindow):
    def __init__(self):
        super().__init__()

        ui_path = resource_path("qsl_design.ui")
        uic.loadUi(ui_path, self)

        self.bg_image_path = None
        self.qso_data = []
        self.worker = None
        self.zoom_factor = 1.0
        self.current_qimage = None

        self.config = {
            "lang": "default",
            "callsign": "LU1ABC",
            "default_bg": "",
            "pos": "bottom_center",
            "opacity": 85,
            "color_h_bg": "#4a4a4a",
            "color_h_txt": "#ffffff",
            "color_d_bg": "#f5f5f5",
            "color_d_txt": "#000000",
            "table_scale": 1.0,
        }

        self.load_config()

        init_i18n(self.config.get("lang", "default"))

        self.setup_ui_elements()
        self.apply_translations()
        self.connect_signals()

        if self.config["default_bg"] and os.path.exists(self.config["default_bg"]):
            self.bg_image_path = self.config["default_bg"]
            self.lbl_bg.setText(os.path.basename(self.bg_image_path))

        self.updater = UpdateChecker(APP_VERSION)
        self.updater.update_available.connect(self.show_update_dialog)
        self.updater.start()

    def setup_ui_elements(self):
        self.table.setColumnCount(8)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setColumnWidth(0, 30)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_menu)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; }")

        layout_preview = self.group_preview.layout()
        layout_preview.removeWidget(self.lbl_preview)

        self.scroll_area.setWidget(self.lbl_preview)
        layout_preview.addWidget(self.scroll_area)

        self.lbl_preview.installEventFilter(self)
        self.lbl_preview.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lbl_preview.customContextMenuRequested.connect(self.show_preview_menu)

    def apply_translations(self):
        self.setWindowTitle(f"{tr('title')} v{APP_VERSION}")

        self.menuArchivo.setTitle(tr("file"))
        self.menuHerramientas.setTitle(tr("tools"))
        self.menuAyuda.setTitle(tr("help"))

        self.actionSalir.setText(tr("exit"))
        self.actionConfiguracion.setText(tr("settings"))
        self.actionAcerca_de.setText(tr("about"))

        self.group_archivos.setTitle(tr("files_group"))

        self.btn_bg.setText(tr("btn_bg"))
        self.btn_adif.setText(tr("btn_adif"))

        if not self.bg_image_path:
            self.lbl_bg.setText(tr("no_img"))

        if not self.qso_data:
            self.lbl_adif.setText(tr("no_adif"))

        self.btn_export.setText(tr("btn_export"))

        self.group_preview.setTitle(tr("preview_group"))

        if self.table.rowCount() == 0:
            self.lbl_preview.setText(tr("preview_hint"))

        self.table.setHorizontalHeaderLabels(tr("headers"))

        self.btn_all.setText(tr("all"))
        self.btn_none.setText(tr("none"))

    def connect_signals(self):
        self.btn_bg.clicked.connect(self.load_background)
        self.btn_adif.clicked.connect(self.load_adif)
        self.btn_export.clicked.connect(self.start_export)

        self.actionSalir.triggered.connect(self.close)
        self.actionConfiguracion.triggered.connect(self.show_settings)
        self.actionAcerca_de.triggered.connect(self.show_about)

        self.btn_all.clicked.connect(
            lambda: self.bulk_check(Qt.CheckState.Checked)
        )
        self.btn_none.clicked.connect(
            lambda: self.bulk_check(Qt.CheckState.Unchecked)
        )

        self.table.itemSelectionChanged.connect(self.on_selection_changed)

        self.table.itemDoubleClicked.connect(
            lambda item: self.table.editItem(item)
            if item.column() > 0 else None
        )

        self.table.itemChanged.connect(self.on_table_item_changed)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.config.update(json.load(f))

                    legacy_mapping = {
                        "Abajo - Centro": "bottom_center",
                        "Abajo - Izquierda": "bottom_left",
                        "Abajo - Derecha": "bottom_right",
                        "Arriba - Centro": "top_center",
                        "Arriba - Izquierda": "top_left",
                        "Arriba - Derecha": "top_right",
                        "Centro Absoluto": "center",
                    }

                    if self.config["pos"] in legacy_mapping:
                        self.config["pos"] = legacy_mapping[self.config["pos"]]

            except Exception as e:
                logger.error(f"Error loading config: {e}")

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(self.config, f)

        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def show_table_menu(self, pos):
        menu = QMenu()

        action_add = menu.addAction(tr("add_row"))
        action_delete = menu.addAction(tr("del_row"))

        if not self.table.selectionModel().hasSelection():
            action_delete.setEnabled(False)

        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        if action == action_add:
            self.add_manual_row()

        elif action == action_delete:
            self.delete_selected_rows()

    def add_manual_row(self):
        row = self.table.rowCount()

        self.table.insertRow(row)

        checkbox = QTableWidgetItem()
        checkbox.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable
            | Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
        )

        checkbox.setCheckState(Qt.CheckState.Checked)

        self.table.setItem(row, 0, checkbox)

        for col in range(1, 8):
            self.table.setItem(row, col, QTableWidgetItem(""))

        self.table.selectRow(row)

    def delete_selected_rows(self):
        rows = sorted(
            set(idx.row() for idx in self.table.selectionModel().selectedRows()),
            reverse=True
        )

        for row in rows:
            self.table.removeRow(row)

        self.on_selection_changed()

    def eventFilter(self, source, event):
            if source == self.lbl_preview:
                if event.type() == QEvent.Type.NativeGesture:
                    if event.gestureType() == Qt.NativeGestureType.ZoomNativeGesture:
                        if not self.current_qimage:
                            return super().eventFilter(source, event)

                        zoom_multiplier = 1.0 + event.value()
                        self.zoom_factor *= zoom_multiplier
                        
                        self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
                        self.update_preview(force_render=False)
                        return True

                elif event.type() == QEvent.Type.Wheel:
                    if not self.current_qimage:
                        return super().eventFilter(source, event)

                    delta = event.angleDelta().y()
                    if delta > 0:
                        self.zoom_factor *= 1.15
                    elif delta < 0:
                        self.zoom_factor /= 1.15

                    self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
                    self.update_preview(force_render=False)
                    return True

            return super().eventFilter(source, event)

    def on_table_item_changed(self, item):
        selected = self.table.selectionModel().selectedRows()

        if selected and selected[0].row() == item.row():
            self.update_preview(force_render=True)

    def bulk_check(self, state):
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)

            if item:
                item.setCheckState(state)

    def on_selection_changed(self):
        self.zoom_factor = 1.0
        self.update_preview(force_render=True)

    def show_settings(self):
        dialog = SettingsDialog(self.config, self)

        if dialog.exec():
            self.config = dialog.get_data()

            self.save_config()

            init_i18n(self.config.get("lang", "default"))

            self.apply_translations()

            if (
                self.config["default_bg"]
                and os.path.exists(self.config["default_bg"])
                and not self.bg_image_path
            ):
                self.bg_image_path = self.config["default_bg"]

                self.lbl_bg.setText(
                    os.path.basename(self.bg_image_path)
                )

            self.on_selection_changed()

    def show_about(self):
        message = (
            f"<h2>{tr('title')}</h2>"
            f"<p>Version: "
            f"<strong>"
            f"<a href=\"https://github.com/igonzalezb/QSL-Card-Generator\" "
            f"style=\"color: #1E90FF;\">{APP_VERSION}</a>"
            f"</strong></p>"
            f"<p>Developed by: <strong>LU2EXV</strong></p>"
        )

        QMessageBox.about(self, tr("about"), message)

    def load_background(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            tr("btn_bg"),
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if filename:
            try:
                img = Image.open(filename)
                w, h = img.size
                
                current_ratio = w / h
                target_ratio = 16 / 9
                
                if abs(current_ratio - target_ratio) > 0.01:
                    
                    reply = QMessageBox.question(
                        self,
                        tr("resize_title"),
                        tr("resize_msg"),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if reply == QMessageBox.StandardButton.Yes:
                        img = ImageOps.fit(img, (1920, 1080), Image.Resampling.LANCZOS)
                        
                        name, ext = os.path.splitext(filename)
                        new_filename = f"{name}_16_9{ext}"
                        
                        if ext.lower() in ['.jpg', '.jpeg']:
                            img.convert("RGB").save(new_filename, "JPEG", quality=95)
                        else:
                            img.save(new_filename)
                            
                        filename = new_filename

            except Exception as e:
                logger.error(f"Error checking aspect ratio: {e}")

            self.bg_image_path = filename
            self.lbl_bg.setText(os.path.basename(filename))
            self.on_selection_changed()

    def load_adif(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            tr("btn_adif"),
            "",
            "ADIF Files (*.adi *.adif)"
        )

        if filename:
            self.lbl_adif.setText(os.path.basename(filename))
            self.populate_table(filename)

    def populate_table(self, filepath):
        try:
            contacts, _ = adif_io.read_from_file(filepath)
            for qso in contacts:
                for key, value in qso.items():
                    if isinstance(value, str):
                        qso[key] = value.replace('\n', '').replace('\r', '').strip()
                        
            self.qso_data = contacts

            self.table.setRowCount(len(contacts))

            self.table.itemChanged.disconnect(self.on_table_item_changed)

            for row, qso in enumerate(contacts):

                checkbox = QTableWidgetItem()

                checkbox.setFlags(
                    Qt.ItemFlag.ItemIsUserCheckable
                    | Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                )

                checkbox.setCheckState(Qt.CheckState.Checked)

                self.table.setItem(row, 0, checkbox)

                self.table.setItem(
                    row,
                    1,
                    QTableWidgetItem(qso.get("CALL", ""))
                )

                date = qso.get("QSO_DATE", "")

                formatted_date = (
                    datetime.datetime.strptime(
                        date,
                        "%Y%m%d"
                    ).strftime("%d/%m/%Y")
                    if len(date) == 8 else date
                )

                self.table.setItem(
                    row,
                    2,
                    QTableWidgetItem(formatted_date)
                )

                time_on = qso.get("TIME_ON", "")

                formatted_time = (
                    f"{time_on[:2]}:{time_on[2:4]} UTC"
                    if len(time_on) >= 4 else time_on
                )

                self.table.setItem(
                    row,
                    3,
                    QTableWidgetItem(formatted_time)
                )

                self.table.setItem(
                    row,
                    4,
                    QTableWidgetItem(qso.get("BAND", ""))
                )

                self.table.setItem(
                    row,
                    5,
                    QTableWidgetItem(qso.get("MODE", ""))
                )

                freq = qso.get("FREQ", "")

                formatted_freq = (
                    f"{float(freq):.3f} MHz"
                    if freq.replace(".", "", 1).isdigit()
                    else freq
                )

                self.table.setItem(
                    row,
                    6,
                    QTableWidgetItem(formatted_freq)
                )

                self.table.setItem(
                    row,
                    7,
                    QTableWidgetItem(qso.get("RST_SENT", ""))
                )

            self.table.itemChanged.connect(
                self.on_table_item_changed
            )

            if self.table.rowCount() > 0:
                self.table.selectRow(0)

            logger.info(
                f"ADIF loaded: {len(contacts)} contacts."
            )

        except Exception as e:
            logger.error(f"Error parsing ADIF: {e}")

            QMessageBox.critical(
                self,
                "Error",
                f"ADIF Error:\n{str(e)}"
            )

    def update_preview(self, force_render=True):

        if not self.bg_image_path or self.table.rowCount() == 0:
            self.lbl_preview.setText(tr("preview_hint"))
            return

        selected = self.table.selectionModel().selectedRows()

        if not selected:
            return

        if force_render:

            row = selected[0].row()

            data = [
                self.table.item(row, col).text()
                if self.table.item(row, col)
                else ""
                for col in range(1, 8)
            ]

            try:
                pil_image, _ = draw_qsl_core(
                    Image.open(self.bg_image_path).convert("RGBA"),
                    self.config,
                    data
                )

                raw_data = pil_image.convert("RGBA").tobytes(
                    "raw",
                    "RGBA"
                )

                self.current_qimage = QImage(
                    raw_data,
                    pil_image.width,
                    pil_image.height,
                    QImage.Format.Format_RGBA8888
                )

            except Exception:
                self.lbl_preview.setText(
                    f"Preview Error: {tr('err_call')}"
                )

                self.current_qimage = None

                return

        if self.current_qimage:

            viewport_w = max(
                self.scroll_area.viewport().width(),
                100
            )

            viewport_h = max(
                self.scroll_area.viewport().height(),
                100
            )

            base_scaled = self.current_qimage.scaled(
                viewport_w,
                viewport_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            target_w = int(base_scaled.width() * self.zoom_factor)
            target_h = int(base_scaled.height() * self.zoom_factor)

            final_pixmap = QPixmap.fromImage(
                self.current_qimage
            ).scaled(
                target_w,
                target_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            self.lbl_preview.setPixmap(final_pixmap)

            if self.zoom_factor > 1.0:
                self.scroll_area.setWidgetResizable(False)
                self.lbl_preview.resize(final_pixmap.size())

            else:
                self.scroll_area.setWidgetResizable(True)

    def resizeEvent(self, event):

        if hasattr(self, "zoom_factor"):
            self.update_preview(force_render=False)

        super().resizeEvent(event)

    def start_export(self):

        if not self.bg_image_path or self.table.rowCount() == 0:
            QMessageBox.warning(
                self,
                tr("msg_warn"),
                tr("msg_no_bg")
            )

            return

        output_dir = QFileDialog.getExistingDirectory(self, "")

        if not output_dir:
            return

        export_data = []

        for row in range(self.table.rowCount()):

            if (
                self.table.item(row, 0).checkState()
                == Qt.CheckState.Checked
            ):

                data = [
                    self.table.item(row, col).text()
                    if self.table.item(row, col)
                    else ""
                    for col in range(1, 8)
                ]

                export_data.append({
                    "row": row,
                    "data": data
                })

        if not export_data:
            return

        self.progress_dialog = QProgressDialog(
            tr("exporting"),
            tr("wait"),
            0,
            len(export_data),
            self
        )

        self.progress_dialog.setWindowModality(
            Qt.WindowModality.WindowModal
        )

        self.progress_dialog.show()

        self.worker = ExportWorker(
            self.bg_image_path,
            self.config,
            export_data,
            output_dir
        )

        self.worker.progress.connect(
            self.progress_dialog.setValue
        )

        self.worker.finished_export.connect(
            self.export_finished
        )

        self.worker.start()

    def export_finished(self, processed, errors):

        self.progress_dialog.close()

        message = f"{processed} {tr('msg_done')}"

        if errors:

            message += (
                "\n\nErrors:\n"
                + "\n".join(errors[:5])
            )

            QMessageBox.warning(
                self,
                tr("res_title"),
                message
            )

        else:

            QMessageBox.information(
                self,
                tr("msg_success"),
                message
            )

    def show_update_dialog(self, version, url):
        """
        Shows an update dialog and opens the browser
        if the user accepts.
        """

        message = tr("update_msg").replace(
            "{version}",
            version
        )

        reply = QMessageBox.question(
            self,
            tr("update_title"),
            message,
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(url))
    def show_preview_menu(self, pos):
        if not self.current_qimage:
            return

        menu = QMenu()

        action_zoom_in = menu.addAction(tr("zoom_in"))
        action_zoom_out = menu.addAction(tr("zoom_out"))
        menu.addSeparator()
        action_zoom_fit = menu.addAction(tr("zoom_fit"))

        action = menu.exec(self.lbl_preview.mapToGlobal(pos))

        if action == action_zoom_in:
            self.zoom_factor *= 1.15
            self.zoom_factor = min(self.zoom_factor, 5.0)
            self.update_preview(force_render=False)

        elif action == action_zoom_out:
            self.zoom_factor /= 1.15
            self.zoom_factor = max(0.1, self.zoom_factor)
            self.update_preview(force_render=False)

        elif action == action_zoom_fit:
            self.zoom_factor = 1.0
            self.update_preview(force_render=False)