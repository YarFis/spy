# -*- coding: utf-8 -*-
import urllib.request
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

BOT_TOKEN = "8994337587:AAEMVEneQh_rJe1FNK_08NWBp8TbrKRXIOg"
CHAT_ID   = "345019436"


class FetchThread(QThread):
    messages_ready = pyqtSignal(list)

    def __init__(self, offset=0):
        super().__init__()
        self.offset = offset

    def run(self):
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={self.offset}&timeout=5"
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read())
            results = data.get("result", [])
            msgs = []
            for r in results:
                msg = r.get("message", {})
                if str(msg.get("chat", {}).get("id")) == CHAT_ID:
                    msgs.append({
                        "id": r["update_id"],
                        "text": msg.get("text", ""),
                        "date": msg.get("date", 0),
                    })
            self.messages_ready.emit(msgs)
        except Exception:
            self.messages_ready.emit([])


class MessageCard(QFrame):
    add_device = pyqtSignal(dict)

    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            "QFrame{background:#181825;border:1px solid #313244;"
            "border-radius:10px;}"
        )
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # Парсим текст
        lines = text.strip().split("\n")
        info = {}
        for line in lines:
            if ":" in line:
                k, v = line.split(":", 1)
                info[k.strip()] = v.strip()

        is_device = "[NEW DEVICE]" in text

        if is_device:
            # Заголовок
            title = QLabel("Новое устройство")
            title.setStyleSheet("color:#a6e3a1; font-size:13px; font-weight:bold;")
            layout.addWidget(title)

            # Данные
            for line in lines[1:]:
                if line.strip():
                    lbl = QLabel(line.strip())
                    lbl.setStyleSheet("color:#cdd6f4; font-size:13px; font-family:monospace;")
                    layout.addWidget(lbl)

            # Кнопка добавить
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            add_btn = QPushButton("+ Добавить в список")
            add_btn.setFixedHeight(30)
            add_btn.setStyleSheet(
                "QPushButton{background:#89b4fa;color:#1e1e2e;border-radius:6px;"
                "font-size:12px;font-weight:bold;padding:0 12px;}"
                "QPushButton:hover{background:#b4d0ff;}"
            )

            host = info.get("Local IP", "")
            port_str = info.get("Port", "8765")
            hostname = info.get("Host", "Unknown")
            try:
                port = int(port_str)
            except ValueError:
                port = 8765

            add_btn.clicked.connect(lambda: self.add_device.emit({
                "name": hostname,
                "host": host,
                "port": port,
                "password": "changeme",
            }))
            btn_row.addWidget(add_btn)
            layout.addLayout(btn_row)
        else:
            lbl = QLabel(text)
            lbl.setStyleSheet("color:#cdd6f4; font-size:13px;")
            lbl.setWordWrap(True)
            layout.addWidget(lbl)


class InboxWidget(QWidget):
    add_device_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._offset = 0
        self._seen_ids = set()
        self._build_ui()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._fetch)
        self._timer.start(15000)  # проверяем каждые 15 секунд
        self._fetch()  # сразу при открытии

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Шапка
        header = QFrame()
        header.setFixedHeight(48)
        header.setStyleSheet("background:#181825; border-bottom:1px solid #313244;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 0, 16, 0)

        title = QLabel("Входящие")
        title.setStyleSheet("color:#cdd6f4; font-size:15px; font-weight:bold;")
        hl.addWidget(title, 1)

        self.badge = QLabel("")
        self.badge.setStyleSheet(
            "background:#f38ba8; color:#1e1e2e; border-radius:9px;"
            "padding:1px 7px; font-size:11px; font-weight:bold;"
        )
        self.badge.setVisible(False)
        hl.addWidget(self.badge)

        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(32, 32)
        refresh_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border-radius:6px;font-size:16px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        refresh_btn.clicked.connect(self._fetch)
        hl.addWidget(refresh_btn)

        layout.addWidget(header)

        # Список сообщений
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea{border:none; background:#1e1e2e;}")

        self._content = QWidget()
        self._content.setStyleSheet("background:#1e1e2e;")
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(10)
        self._content_layout.addStretch()

        self._empty_lbl = QLabel("Нет входящих сообщений.\nКак только пользователь запустит программу —\nздесь появится его устройство.")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setStyleSheet("color:#45475a; font-size:13px;")
        self._content_layout.insertWidget(0, self._empty_lbl)

        scroll.setWidget(self._content)
        layout.addWidget(scroll, 1)

    def _fetch(self):
        self._thread = FetchThread(self._offset)
        self._thread.messages_ready.connect(self._on_messages)
        self._thread.start()

    def _on_messages(self, messages: list):
        new = [m for m in messages if m["id"] not in self._seen_ids]
        if not new:
            return

        self._empty_lbl.setVisible(False)

        for msg in new:
            self._seen_ids.add(msg["id"])
            self._offset = max(self._offset, msg["id"] + 1)

            card = MessageCard(msg["text"])
            card.add_device.connect(self.add_device_requested.emit)
            self._content_layout.insertWidget(
                self._content_layout.count() - 1, card
            )

        count = len(self._seen_ids)
        self.badge.setText(str(count))
        self.badge.setVisible(True)
