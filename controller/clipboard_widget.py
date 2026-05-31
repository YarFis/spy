from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QGuiApplication


class ClipboardWidget(QWidget):
    send_event = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        layout.addWidget(QLabel("Буфер обмена удалённого ПК:"))

        self.remote_text = QTextEdit()
        self.remote_text.setPlaceholderText("Здесь отобразится буфер удалённого ПК…")
        self.remote_text.setMaximumHeight(120)
        self.remote_text.setStyleSheet(
            "QTextEdit{background:#181825;color:#cdd6f4;border:1px solid #313244;"
            "border-radius:5px;font-size:13px;padding:4px;}"
        )
        layout.addWidget(self.remote_text)

        btn_row = QHBoxLayout()

        get_btn = self._btn("Получить ↓")
        get_btn.clicked.connect(lambda: self.send_event.emit({"type": "clipboard_get"}))
        btn_row.addWidget(get_btn)

        push_btn = self._btn("Отправить ↑")
        push_btn.clicked.connect(self._push_clipboard)
        btn_row.addWidget(push_btn)

        copy_btn = self._btn("Копировать у себя")
        copy_btn.clicked.connect(self._copy_local)
        btn_row.addWidget(copy_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.status = QLabel("")
        self.status.setStyleSheet("color:#6c7086;font-size:12px;")
        layout.addWidget(self.status)

    def _btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(30)
        btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:5px;font-size:12px;padding:0 10px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        return btn

    def _push_clipboard(self):
        text = self.remote_text.toPlainText()
        self.send_event.emit({"type": "clipboard_set", "text": text})
        self.status.setText("Отправлено на удалённый ПК")

    def _copy_local(self):
        text = self.remote_text.toPlainText()
        QGuiApplication.clipboard().setText(text)
        self.status.setText("Скопировано в локальный буфер")

    def handle_message(self, msg: dict):
        t = msg.get("type")
        if t in ("clipboard_data", "clipboard_changed"):
            text = msg.get("text", "")
            self.remote_text.setPlainText(text)
            if t == "clipboard_changed":
                self.status.setText("Буфер удалённого ПК изменился")
