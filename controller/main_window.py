from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QStatusBar, QFrame,
    QCheckBox, QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from viewer import ScreenViewer
from connection import ConnectionWorker
from file_panel import FilePanel
from clipboard_widget import ClipboardWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test — Remote Admin")
        self.resize(1400, 860)
        self.worker: ConnectionWorker | None = None
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Панель подключения
        toolbar = QFrame()
        toolbar.setFixedHeight(52)
        toolbar.setStyleSheet("background:#1e1e2e; border-bottom:1px solid #313244;")
        tl = QHBoxLayout(toolbar)
        tl.setContentsMargins(12, 6, 12, 6)
        tl.setSpacing(8)

        label_style = "color:#cdd6f4; font-size:13px;"

        tl.addWidget(self._label("Хост:", label_style))
        self.host_input = self._input("192.168.1.100", 160)
        tl.addWidget(self.host_input)

        tl.addWidget(self._label("Порт:", label_style))
        self.port_input = self._input("8765", 70)
        tl.addWidget(self.port_input)

        tl.addWidget(self._label("Пароль:", label_style))
        self.pass_input = self._input("", 140, password=True)
        tl.addWidget(self.pass_input)

        self.tls_check = QCheckBox("TLS")
        self.tls_check.setChecked(True)
        self.tls_check.setStyleSheet("color:#cdd6f4; font-size:13px;")
        tl.addWidget(self.tls_check)

        self.connect_btn = QPushButton("Подключить")
        self.connect_btn.setFixedSize(120, 34)
        self.connect_btn.setStyleSheet(self._connect_style())
        self.connect_btn.clicked.connect(self._toggle_connection)
        tl.addWidget(self.connect_btn)

        tl.addStretch()

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color:#45475a; font-size:18px;")
        tl.addWidget(self.status_dot)

        layout.addWidget(toolbar)

        # Основной сплиттер: экран слева, инструменты справа
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle{background:#313244; width:3px;}")

        # Экран
        self.viewer = ScreenViewer()
        self.viewer.setStyleSheet("background:#11111b;")
        self.viewer.mouse_event.connect(self._on_input)
        self.viewer.key_event.connect(self._on_input)
        splitter.addWidget(self.viewer)

        # Правая панель с вкладками
        right = QWidget()
        right.setMinimumWidth(360)
        right.setMaximumWidth(500)
        right.setStyleSheet("background:#1e1e2e;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            "QTabWidget::pane{border:none;background:#1e1e2e;}"
            "QTabBar::tab{background:#181825;color:#6c7086;padding:8px 16px;font-size:13px;}"
            "QTabBar::tab:selected{background:#1e1e2e;color:#cdd6f4;border-bottom:2px solid #89b4fa;}"
        )

        self.file_panel = FilePanel()
        self.file_panel.send_event.connect(self._on_input)
        tabs.addTab(self.file_panel, "Файлы")

        self.clipboard_widget = ClipboardWidget()
        self.clipboard_widget.send_event.connect(self._on_input)
        tabs.addTab(self.clipboard_widget, "Буфер")

        right_layout.addWidget(tabs)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("background:#1e1e2e; color:#6c7086; font-size:12px;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Не подключено")

    def _label(self, text: str, style: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(style)
        return lbl

    def _input(self, placeholder: str, width: int, password: bool = False) -> QLineEdit:
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedWidth(width)
        inp.setFixedHeight(32)
        if password:
            inp.setEchoMode(QLineEdit.EchoMode.Password)
        inp.setStyleSheet(
            "QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:5px;padding:0 8px;font-size:13px;}"
            "QLineEdit:focus{border:1px solid #89b4fa;}"
        )
        return inp

    def _connect_style(self) -> str:
        return (
            "QPushButton{background:#89b4fa;color:#1e1e2e;border-radius:6px;"
            "font-weight:bold;font-size:13px;}"
            "QPushButton:hover{background:#b4d0ff;}"
            "QPushButton:disabled{background:#45475a;color:#6c7086;}"
        )

    def _disconnect_style(self) -> str:
        return (
            "QPushButton{background:#f38ba8;color:#1e1e2e;border-radius:6px;"
            "font-weight:bold;font-size:13px;}"
            "QPushButton:hover{background:#ffb3c1;}"
        )

    def _toggle_connection(self):
        if self.worker and self.worker.isRunning():
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        host = self.host_input.text().strip() or "127.0.0.1"
        port = int(self.port_input.text().strip() or "8765")
        password = self.pass_input.text()

        self.worker = ConnectionWorker(host, port, password, use_tls=self.tls_check.isChecked())
        self.worker.frame_received.connect(self.viewer.update_frame)
        self.worker.message_received.connect(self._on_server_message)
        self.worker.connected.connect(self._on_connected)
        self.worker.disconnected.connect(self._on_disconnected)
        self.worker.error.connect(self._on_error)
        self.worker.start()

        self.connect_btn.setEnabled(False)
        self.status_bar.showMessage(f"Подключение к {host}:{port}…")

    def _disconnect(self):
        if self.worker:
            self.worker.disconnect()

    def _on_connected(self, info: dict):
        monitors = info.get("monitors", [])
        self.status_dot.setStyleSheet("color:#a6e3a1; font-size:18px;")
        self.connect_btn.setText("Отключить")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setStyleSheet(self._disconnect_style())
        mon_info = f"  |  Мониторов: {len(monitors)}" if monitors else ""
        self.status_bar.showMessage(f"Подключено{mon_info}")
        # Загружаем корневую папку при подключении
        self._on_input({"type": "dir_list", "path": "C:\\"})

    def _on_disconnected(self, reason: str):
        self.status_dot.setStyleSheet("color:#45475a; font-size:18px;")
        self.connect_btn.setText("Подключить")
        self.connect_btn.setEnabled(True)
        self.connect_btn.setStyleSheet(self._connect_style())
        self.status_bar.showMessage(reason)

    def _on_error(self, msg: str):
        self.status_bar.showMessage(f"Ошибка: {msg}")
        self._on_disconnected("Отключено из-за ошибки")

    def _on_server_message(self, msg: dict):
        self.file_panel.handle_message(msg)
        self.clipboard_widget.handle_message(msg)

    def _on_input(self, event: dict):
        if self.worker:
            self.worker.send_event(event)

    def closeEvent(self, event):
        self._disconnect()
        super().closeEvent(event)
