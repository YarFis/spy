"""
Окно сессии — открывается при подключении к устройству.
Показывает экран удалённого ПК.
Кнопка «Перехватить» видна только администратору (в правом нижнем углу).
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QPushButton,
    QLabel, QStatusBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QRect, pyqtProperty
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

from viewer import ScreenViewer
from connection import ConnectionWorker
from file_panel import FilePanel
from clipboard_widget import ClipboardWidget


class SessionWindow(QMainWindow):
    def __init__(self, device: dict, parent=None):
        super().__init__(parent)
        self.device = device
        self.worker: ConnectionWorker | None = None
        self._controlling = False  # режим управления

        self.setWindowTitle(f"Test — {device['name']}")
        self.resize(1280, 800)
        self.setMinimumSize(640, 480)
        self.setStyleSheet("background:#11111b;")

        self._build_ui()
        self._connect()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background:#11111b;")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Экран удалённого ПК — занимает всё окно
        self.viewer = ScreenViewer()
        self.viewer.mouse_event.connect(self._forward_if_controlling)
        self.viewer.key_event.connect(self._forward_if_controlling)
        layout.addWidget(self.viewer, 1)

        # Статус-бар
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(
            "background:rgba(30,30,46,200); color:#6c7086; font-size:12px;"
        )
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Подключение…")

        # Кнопка «Перехватить» — плавающая, поверх всего, правый нижний угол
        self._intercept_btn = QPushButton("⚡ Перехватить", central)
        self._intercept_btn.setFixedSize(148, 40)
        self._intercept_btn.setStyleSheet(self._intercept_idle_style())
        self._intercept_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._intercept_btn.clicked.connect(self._toggle_control)
        self._intercept_btn.raise_()

        # Подсказка: F11 — полный экран, Esc — выход из управления
        QShortcut(QKeySequence("F11"), self, activated=self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, activated=self._release_control)

        self._position_intercept_btn()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_intercept_btn()

    def _position_intercept_btn(self):
        btn = self._intercept_btn
        margin = 16
        x = self.centralWidget().width() - btn.width() - margin
        y = self.centralWidget().height() - btn.height() - margin - self.status_bar.height()
        btn.move(x, y)

    # ─── Подключение ──────────────────────────────────────────────────────────

    def _connect(self):
        d = self.device
        self.worker = ConnectionWorker(
            d["host"], int(d.get("port", 8765)),
            d.get("password", ""),
            use_tls=True
        )
        self.worker.frame_received.connect(self.viewer.update_frame)
        self.worker.message_received.connect(self._on_message)
        self.worker.connected.connect(self._on_connected)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    def _on_connected(self, info: dict):
        monitors = info.get("monitors", [])
        mon = f" | Мониторов: {len(monitors)}" if monitors else ""
        self.status_bar.showMessage(f"Подключено — {self.device['name']}{mon}   |   F11 — полный экран")
        self._intercept_btn.setVisible(True)

    def _on_disconnected(self, reason: str):
        self.status_bar.showMessage(f"Отключено: {reason}")
        self._intercept_btn.setVisible(False)
        self._controlling = False

    def _on_error(self, msg: str):
        self.status_bar.showMessage(f"Ошибка: {msg}")
        self._intercept_btn.setVisible(False)

    def _on_message(self, msg: dict):
        # Передаём в будущие панели (файлы, буфер) если понадобится
        pass

    # ─── Управление ───────────────────────────────────────────────────────────

    def _toggle_control(self):
        if self._controlling:
            self._release_control()
        else:
            self._take_control()

    def _take_control(self):
        if not self.worker:
            return
        self._controlling = True
        # Говорим агенту заблокировать физический ввод
        self.worker.send_event({"type": "take_control"})
        self._intercept_btn.setText("✋ Отдать управление")
        self._intercept_btn.setStyleSheet(self._intercept_active_style())
        self.viewer.setFocus()
        self.status_bar.showMessage(
            f"Управление активно — {self.device['name']}   |   Esc — отдать управление"
        )

    def _release_control(self):
        if not self._controlling:
            return
        self._controlling = False
        if self.worker:
            self.worker.send_event({"type": "release_control"})
        self._intercept_btn.setText("⚡ Перехватить")
        self._intercept_btn.setStyleSheet(self._intercept_idle_style())
        self.status_bar.showMessage(f"Наблюдение — {self.device['name']}")

    def _forward_if_controlling(self, event: dict):
        """Ввод передаётся агенту только в режиме управления."""
        if self._controlling and self.worker:
            self.worker.send_event(event)

    # ─── Полный экран ─────────────────────────────────────────────────────────

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    # ─── Стили кнопки ─────────────────────────────────────────────────────────

    @staticmethod
    def _intercept_idle_style() -> str:
        return (
            "QPushButton{"
            "background:rgba(137,180,250,220);"
            "color:#1e1e2e;"
            "border-radius:10px;"
            "font-weight:bold;"
            "font-size:13px;"
            "border:none;"
            "}"
            "QPushButton:hover{"
            "background:rgba(180,208,255,240);"
            "}"
        )

    @staticmethod
    def _intercept_active_style() -> str:
        return (
            "QPushButton{"
            "background:rgba(243,139,168,230);"
            "color:#1e1e2e;"
            "border-radius:10px;"
            "font-weight:bold;"
            "font-size:13px;"
            "border:none;"
            "}"
            "QPushButton:hover{"
            "background:rgba(255,179,193,240);"
            "}"
        )

    def closeEvent(self, event):
        self._release_control()
        if self.worker:
            self.worker.disconnect()
        super().closeEvent(event)
