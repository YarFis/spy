import os
import hashlib
import uuid
import base64
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QFileDialog, QProgressBar,
    QLineEdit, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

CHUNK_SIZE = 256 * 1024


class FilePanel(QWidget):
    send_event = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = "C:\\"
        self._downloads: dict[str, dict] = {}
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Адресная строка
        addr_row = QHBoxLayout()
        self.path_input = QLineEdit("C:\\")
        self.path_input.setStyleSheet(
            "QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:5px;padding:0 8px;font-size:13px;}"
        )
        self.path_input.returnPressed.connect(self._navigate)
        addr_row.addWidget(self.path_input)

        go_btn = self._btn("→", 36)
        go_btn.clicked.connect(self._navigate)
        addr_row.addWidget(go_btn)
        layout.addLayout(addr_row)

        # Дерево файлов удалённого ПК
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Имя", "Размер"])
        self.tree.setColumnWidth(0, 260)
        self.tree.setStyleSheet(
            "QTreeWidget{background:#181825;color:#cdd6f4;border:1px solid #313244;"
            "font-size:13px;}"
            "QTreeWidget::item:selected{background:#45475a;}"
            "QHeaderView::section{background:#1e1e2e;color:#6c7086;border:none;padding:4px;}"
        )
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.tree, 1)

        # Прогресс
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setStyleSheet(
            "QProgressBar{background:#313244;border-radius:4px;height:8px;text-align:center;color:#cdd6f4;}"
            "QProgressBar::chunk{background:#89b4fa;border-radius:4px;}"
        )
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("color:#6c7086; font-size:12px;")
        layout.addWidget(self.status_lbl)

        # Кнопки
        btn_row = QHBoxLayout()
        upload_btn = self._btn("Загрузить на ПК ↑", 160)
        upload_btn.clicked.connect(self._upload)
        download_btn = self._btn("Скачать ↓", 120)
        download_btn.clicked.connect(self._download)
        btn_row.addWidget(upload_btn)
        btn_row.addWidget(download_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _btn(self, text: str, width: int) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setFixedWidth(width)
        btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:5px;font-size:13px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        return btn

    def _navigate(self):
        path = self.path_input.text().strip()
        self.send_event.emit({"type": "dir_list", "path": path})

    def handle_message(self, msg: dict):
        t = msg.get("type")

        if t == "dir_list":
            self._populate_tree(msg)

        elif t == "file_begin_ack":
            pass  # загрузка подтверждена — чанки уже в очереди

        elif t == "file_progress":
            self.progress.setValue(msg.get("progress", 0))

        elif t == "file_done":
            self.progress.setVisible(False)
            self.status_lbl.setText(f"Готово: {msg.get('path', '')}")

        elif t == "file_error":
            self.progress.setVisible(False)
            self.status_lbl.setText(f"Ошибка: {msg.get('reason', '')}")

        elif t == "file_send_begin":
            # Агент начинает слать файл нам
            self._downloads[msg["path"]] = {
                "name": msg["name"],
                "size": msg["size"],
                "chunks": msg["chunks"],
                "md5": msg["md5"],
                "data": [],
            }
            self.progress.setMaximum(msg["chunks"])
            self.progress.setValue(0)
            self.progress.setVisible(True)
            self.status_lbl.setText(f"Скачивается: {msg['name']}")

        elif t == "file_chunk":
            dl = self._downloads.get(msg.get("path"))
            if dl:
                dl["data"].append(base64.b64decode(msg["data"]))
                self.progress.setValue(len(dl["data"]))

                if len(dl["data"]) == dl["chunks"]:
                    self._save_download(msg["path"], dl)

    def _populate_tree(self, msg: dict):
        self._current_path = msg["path"]
        self.path_input.setText(msg["path"])
        self.tree.clear()

        # Кнопка "назад"
        if msg["path"] not in ("C:\\", "D:\\", "/"):
            up = QTreeWidgetItem(["[..]", ""])
            up.setData(0, Qt.ItemDataRole.UserRole, {"is_dir": True, "up": True})
            self.tree.addTopLevelItem(up)

        for entry in sorted(msg.get("entries", []), key=lambda e: (not e["is_dir"], e["name"].lower())):
            size_str = self._fmt_size(entry["size"]) if not entry["is_dir"] else ""
            item = QTreeWidgetItem([entry["name"], size_str])
            item.setData(0, Qt.ItemDataRole.UserRole, entry)
            self.tree.addTopLevelItem(item)

    def _on_double_click(self, item: QTreeWidgetItem, _col: int):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return
        if data.get("up"):
            parent = str(Path(self._current_path).parent)
            self.send_event.emit({"type": "dir_list", "path": parent})
        elif data.get("is_dir"):
            new_path = str(Path(self._current_path) / data["name"])
            self.send_event.emit({"type": "dir_list", "path": new_path})

    def _upload(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выбери файлы для загрузки")
        if not files:
            return
        for src in files:
            self._do_upload(src)

    def _do_upload(self, src: str):
        p = Path(src)
        dest = str(Path(self._current_path) / p.name)
        data = p.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        chunks_data = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
        tid = str(uuid.uuid4())[:8]

        self.send_event.emit({
            "type": "file_begin",
            "id": tid,
            "dest": dest,
            "size": len(data),
            "chunks": len(chunks_data),
        })
        for idx, chunk in enumerate(chunks_data):
            self.send_event.emit({
                "type": "file_chunk",
                "id": tid,
                "index": idx,
                "data": base64.b64encode(chunk).decode(),
            })
        self.send_event.emit({"type": "file_finish", "id": tid, "md5": md5})

        self.progress.setMaximum(100)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.status_lbl.setText(f"Отправка: {p.name}")

    def _download(self):
        item = self.tree.currentItem()
        if not item:
            return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("is_dir"):
            return
        remote_path = str(Path(self._current_path) / data["name"])
        self.send_event.emit({"type": "file_download", "path": remote_path})

    def _save_download(self, remote_path: str, dl: dict):
        save_path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", dl["name"])
        if not save_path:
            return
        content = b"".join(dl["data"])
        if hashlib.md5(content).hexdigest() != dl["md5"]:
            self.status_lbl.setText("Ошибка: контрольная сумма не совпадает")
            return
        Path(save_path).write_bytes(content)
        self.progress.setVisible(False)
        self.status_lbl.setText(f"Сохранено: {save_path}")
        del self._downloads[remote_path]

    @staticmethod
    def _fmt_size(size: int) -> str:
        for unit in ("Б", "КБ", "МБ", "ГБ"):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"
