# -*- coding: utf-8 -*-
import json
import pathlib
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QMessageBox, QFrame, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon

DEVICES_FILE = pathlib.Path.home() / ".test_admin" / "devices.json"


def load_devices() -> list[dict]:
    if DEVICES_FILE.exists():
        try:
            return json.loads(DEVICES_FILE.read_text("utf-8"))
        except Exception:
            pass
    return []


def save_devices(devices: list[dict]):
    DEVICES_FILE.parent.mkdir(parents=True, exist_ok=True)
    DEVICES_FILE.write_text(json.dumps(devices, ensure_ascii=False, indent=2), "utf-8")


class AddDeviceDialog(QDialog):
    def __init__(self, parent=None, device=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить устройство" if not device else "Редактировать устройство")
        self.setFixedSize(400, 280)
        self.setStyleSheet("background:#1e1e2e; color:#cdd6f4;")

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Добавить устройство" if not device else "Редактировать устройство")
        title.setStyleSheet("font-size:16px; font-weight:bold; color:#cdd6f4;")
        layout.addWidget(title)

        hint = QLabel("Узнайте IP-адрес компьютера: Пуск → cmd → ipconfig")
        hint.setStyleSheet("font-size:11px; color:#6c7086;")
        layout.addWidget(hint)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        inp_style = (
            "QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:6px;padding:6px 10px;font-size:13px;}"
            "QLineEdit:focus{border:1px solid #89b4fa;}"
        )
        lbl_style = "color:#a6adc8; font-size:13px;"

        self.name_inp = QLineEdit(device.get("name", "") if device else "")
        self.name_inp.setPlaceholderText("например: Рабочий компьютер")
        self.name_inp.setStyleSheet(inp_style)
        lbl1 = QLabel("Название:")
        lbl1.setStyleSheet(lbl_style)
        form.addRow(lbl1, self.name_inp)

        self.host_inp = QLineEdit(device.get("host", "") if device else "")
        self.host_inp.setPlaceholderText("например: 192.168.1.100")
        self.host_inp.setStyleSheet(inp_style)
        lbl2 = QLabel("IP-адрес:")
        lbl2.setStyleSheet(lbl_style)
        form.addRow(lbl2, self.host_inp)

        self.port_inp = QLineEdit(str(device.get("port", "8765")) if device else "8765")
        self.port_inp.setStyleSheet(inp_style)
        lbl3 = QLabel("Порт:")
        lbl3.setStyleSheet(lbl_style)
        form.addRow(lbl3, self.port_inp)

        self.pass_inp = QLineEdit(device.get("password", "") if device else "")
        self.pass_inp.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_inp.setPlaceholderText("пароль доступа")
        self.pass_inp.setStyleSheet(inp_style)
        lbl4 = QLabel("Пароль:")
        lbl4.setStyleSheet(lbl_style)
        form.addRow(lbl4, self.pass_inp)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.setSpacing(8)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setFixedHeight(36)
        cancel_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:6px;font-size:13px;padding:0 20px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        cancel_btn.clicked.connect(self.reject)

        ok_btn = QPushButton("Сохранить")
        ok_btn.setFixedHeight(36)
        ok_btn.setStyleSheet(
            "QPushButton{background:#89b4fa;color:#1e1e2e;border-radius:6px;"
            "font-size:13px;font-weight:bold;padding:0 20px;}"
            "QPushButton:hover{background:#b4d0ff;}"
        )
        ok_btn.clicked.connect(self.accept)

        btns.addStretch()
        btns.addWidget(cancel_btn)
        btns.addWidget(ok_btn)
        layout.addLayout(btns)

    def get_device(self) -> dict:
        name = self.name_inp.text().strip()
        host = self.host_inp.text().strip()
        if not name or not host:
            QMessageBox.warning(self, "Ошибка", "Заполните название и IP-адрес.")
            return None
        try:
            port = int(self.port_inp.text().strip())
        except ValueError:
            port = 8765
        return {
            "name": name,
            "host": host,
            "port": port,
            "password": self.pass_inp.text(),
        }


class DeviceCard(QWidget):
    def __init__(self, device: dict):
        super().__init__()
        self.device = device
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        # Иконка
        icon_lbl = QLabel("🖥")
        icon_lbl.setFixedSize(36, 36)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            "background:#313244; border-radius:8px; font-size:18px;"
        )
        layout.addWidget(icon_lbl)

        # Информация
        info = QVBoxLayout()
        info.setSpacing(2)
        name_lbl = QLabel(device["name"])
        name_lbl.setStyleSheet("color:#cdd6f4; font-size:14px; font-weight:bold;")
        addr_lbl = QLabel(f"{device['host']}:{device['port']}")
        addr_lbl.setStyleSheet("color:#6c7086; font-size:12px;")
        info.addWidget(name_lbl)
        info.addWidget(addr_lbl)
        layout.addLayout(info, 1)

        # Статус
        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color:#45475a; font-size:16px;")
        layout.addWidget(self.status_dot)


class DeviceListWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Remote Admin")
        self.setFixedSize(520, 640)
        self.devices = load_devices()
        self._selected_index = None
        self._sessions = []
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background:#1e1e2e;")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Вкладки
        from inbox import InboxWidget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane{border:none;}"
            "QTabBar::tab{background:#181825;color:#6c7086;padding:10px 24px;font-size:13px;}"
            "QTabBar::tab:selected{background:#1e1e2e;color:#cdd6f4;border-bottom:2px solid #89b4fa;}"
        )

        # Страница устройств
        devices_page = QWidget()
        devices_page.setStyleSheet("background:#1e1e2e;")
        self._devices_layout = QVBoxLayout(devices_page)
        self._devices_layout.setContentsMargins(0, 0, 0, 0)
        self._devices_layout.setSpacing(0)
        self._tabs.addTab(devices_page, "Устройства")

        # Страница входящих
        self._inbox = InboxWidget()
        self._inbox.add_device_requested.connect(self._add_from_inbox)
        self._tabs.addTab(self._inbox, "Входящие")

        layout.addWidget(self._tabs)

        # Далее весь UI идёт в devices_page
        layout = self._devices_layout

        # Шапка
        header = QFrame()
        header.setFixedHeight(72)
        header.setStyleSheet("background:#181825; border-bottom:1px solid #313244;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(20, 0, 20, 0)

        title_lbl = QLabel("Remote Admin")
        title_lbl.setStyleSheet("color:#cdd6f4; font-size:20px; font-weight:bold;")
        sub_lbl = QLabel("Выберите устройство для подключения")
        sub_lbl.setStyleSheet("color:#6c7086; font-size:12px;")

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        hl.addLayout(title_col, 1)

        add_btn = QPushButton("+ Добавить")
        add_btn.setFixedSize(110, 36)
        add_btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:6px;font-size:13px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        add_btn.clicked.connect(self._add_device)
        hl.addWidget(add_btn)
        layout.addWidget(header)

        # Список устройств
        body = QWidget()
        body.setStyleSheet("background:#1e1e2e;")
        bl = QVBoxLayout(body)
        bl.setContentsMargins(16, 16, 16, 8)
        bl.setSpacing(8)

        devices_lbl = QLabel("Устройства")
        devices_lbl.setStyleSheet("color:#6c7086; font-size:12px; font-weight:bold;")
        bl.addWidget(devices_lbl)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget{background:#181825;border:1px solid #313244;"
            "border-radius:10px; outline:none;}"
            "QListWidget::item{border-bottom:1px solid #252535; padding:0;}"
            "QListWidget::item:last-child{border-bottom:none;}"
            "QListWidget::item:selected{background:#252540;}"
            "QListWidget::item:hover{background:#252535;}"
        )
        self.list_widget.setSpacing(0)
        self.list_widget.itemSelectionChanged.connect(self._on_selection)
        self.list_widget.itemDoubleClicked.connect(lambda: self._open_session())
        bl.addWidget(self.list_widget, 1)

        # Пустое состояние
        self.empty_lbl = QLabel("Нет устройств.\nНажмите «+ Добавить» чтобы добавить первое.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color:#45475a; font-size:13px;")
        self.empty_lbl.setVisible(False)
        bl.addWidget(self.empty_lbl)

        layout.addWidget(body, 1)

        # Нижняя панель
        footer = QFrame()
        footer.setFixedHeight(80)
        footer.setStyleSheet("background:#181825; border-top:1px solid #313244;")
        fl = QHBoxLayout(footer)
        fl.setContentsMargins(16, 12, 16, 12)
        fl.setSpacing(8)

        self.edit_btn = self._footer_btn("✏  Изменить")
        self.edit_btn.clicked.connect(self._edit_device)
        self.edit_btn.setEnabled(False)

        self.del_btn = self._footer_btn("🗑  Удалить")
        self.del_btn.clicked.connect(self._delete_device)
        self.del_btn.setEnabled(False)

        fl.addWidget(self.edit_btn)
        fl.addWidget(self.del_btn)
        fl.addStretch()

        self.connect_btn = QPushButton("Подключиться  →")
        self.connect_btn.setFixedSize(160, 44)
        self.connect_btn.setVisible(False)
        self.connect_btn.setStyleSheet(
            "QPushButton{background:#89b4fa;color:#1e1e2e;border-radius:8px;"
            "font-weight:bold;font-size:14px;}"
            "QPushButton:hover{background:#b4d0ff;}"
        )
        self.connect_btn.clicked.connect(self._open_session)
        fl.addWidget(self.connect_btn)

        layout.addWidget(footer)

    def _footer_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(36)
        btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:6px;font-size:13px;padding:0 14px;}"
            "QPushButton:hover{background:#45475a;}"
            "QPushButton:disabled{color:#45475a;border-color:#313244;}"
        )
        return btn

    def _refresh_list(self):
        self.list_widget.clear()
        self.empty_lbl.setVisible(len(self.devices) == 0)
        self.list_widget.setVisible(len(self.devices) > 0)
        for device in self.devices:
            item = QListWidgetItem(self.list_widget)
            widget = DeviceCard(device)
            item.setSizeHint(QSize(0, 66))
            self.list_widget.setItemWidget(item, widget)

    def _on_selection(self):
        row = self.list_widget.currentRow()
        self._selected_index = row if row >= 0 else None
        has = self._selected_index is not None
        self.connect_btn.setVisible(has)
        self.edit_btn.setEnabled(has)
        self.del_btn.setEnabled(has)
        if has:
            dev = self.devices[self._selected_index]
            self.connect_btn.setText(f"Подключиться  →")

    def _open_session(self):
        if self._selected_index is None:
            return
        device = self.devices[self._selected_index]
        from session_window import SessionWindow
        win = SessionWindow(device)
        win.show()
        self._sessions.append(win)

    def _add_device(self):
        dlg = AddDeviceDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dev = dlg.get_device()
            if dev:
                self.devices.append(dev)
                save_devices(self.devices)
                self._refresh_list()

    def _edit_device(self):
        if self._selected_index is None:
            return
        dlg = AddDeviceDialog(self, device=self.devices[self._selected_index])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            dev = dlg.get_device()
            if dev:
                self.devices[self._selected_index] = dev
                save_devices(self.devices)
                self._refresh_list()

    def _delete_device(self):
        if self._selected_index is None:
            return
        name = self.devices[self._selected_index]["name"]
        reply = QMessageBox.question(
            self, "Удалить устройство",
            f"Удалить «{name}» из списка?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.devices[self._selected_index]
            save_devices(self.devices)
            self._selected_index = None
            self.connect_btn.setVisible(False)
            self.edit_btn.setEnabled(False)
            self.del_btn.setEnabled(False)
            self._refresh_list()

    def _add_from_inbox(self, device: dict):
        self.devices.append(device)
        save_devices(self.devices)
        self._refresh_list()
        self._tabs.setCurrentIndex(0)
        QMessageBox.information(
            self, "Добавлено",
            f"Устройство «{device['name']}» добавлено в список.\n"
            f"Не забудь указать правильный пароль."
        )
