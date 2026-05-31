"""
Главное окно — список устройств.
Устройства добавляются вручную (имя + IP + порт + пароль).
"""
import json
import pathlib
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox,
    QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

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
    def __init__(self, parent=None, device: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Добавить устройство" if not device else "Редактировать")
        self.setFixedSize(360, 240)
        self.setStyleSheet("background:#1e1e2e; color:#cdd6f4;")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(10)

        inp_style = (
            "QLineEdit{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:5px;padding:4px 8px;font-size:13px;}"
            "QLineEdit:focus{border:1px solid #89b4fa;}"
        )
        lbl_style = "color:#cdd6f4; font-size:13px;"

        self.name_inp = QLineEdit(device.get("name", "") if device else "")
        self.name_inp.setStyleSheet(inp_style)
        lbl = QLabel("Имя:")
        lbl.setStyleSheet(lbl_style)
        form.addRow(lbl, self.name_inp)

        self.host_inp = QLineEdit(device.get("host", "") if device else "")
        self.host_inp.setPlaceholderText("192.168.1.100")
        self.host_inp.setStyleSheet(inp_style)
        lbl2 = QLabel("IP / Хост:")
        lbl2.setStyleSheet(lbl_style)
        form.addRow(lbl2, self.host_inp)

        self.port_inp = QLineEdit(str(device.get("port", "8765")) if device else "8765")
        self.port_inp.setStyleSheet(inp_style)
        lbl3 = QLabel("Порт:")
        lbl3.setStyleSheet(lbl_style)
        form.addRow(lbl3, self.port_inp)

        self.pass_inp = QLineEdit(device.get("password", "") if device else "")
        self.pass_inp.setEchoMode(QLineEdit.EchoMode.Password)
        self.pass_inp.setStyleSheet(inp_style)
        lbl4 = QLabel("Пароль:")
        lbl4.setStyleSheet(lbl_style)
        form.addRow(lbl4, self.pass_inp)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:5px;padding:4px 16px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_device(self) -> dict | None:
        name = self.name_inp.text().strip()
        host = self.host_inp.text().strip()
        if not name or not host:
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


class DeviceItem(QWidget):
    def __init__(self, device: dict):
        super().__init__()
        self.device = device
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)

        dot = QLabel("●")
        dot.setStyleSheet("color:#45475a; font-size:14px;")
        dot.setFixedWidth(20)
        layout.addWidget(dot)
        self.dot = dot

        info = QVBoxLayout()
        name_lbl = QLabel(device["name"])
        name_lbl.setStyleSheet("color:#cdd6f4; font-size:14px; font-weight:bold;")
        addr_lbl = QLabel(f"{device['host']}:{device['port']}")
        addr_lbl.setStyleSheet("color:#6c7086; font-size:12px;")
        info.addWidget(name_lbl)
        info.addWidget(addr_lbl)
        layout.addLayout(info, 1)


class DeviceListWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test — Устройства")
        self.setFixedSize(480, 560)
        self.devices = load_devices()
        self._selected_index: int | None = None
        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        central.setStyleSheet("background:#1e1e2e;")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Заголовок
        title = QLabel("Удалённые устройства")
        title.setStyleSheet("color:#cdd6f4; font-size:18px; font-weight:bold;")
        layout.addWidget(title)

        # Список
        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            "QListWidget{background:#181825;border:1px solid #313244;border-radius:8px;}"
            "QListWidget::item{border-bottom:1px solid #313244;}"
            "QListWidget::item:selected{background:#313244;}"
            "QListWidget::item:hover{background:#252535;}"
        )
        self.list_widget.setSpacing(0)
        self.list_widget.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self.list_widget, 1)

        # Кнопка "Подключиться" — показывается при выборе устройства
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setFixedHeight(44)
        self.connect_btn.setVisible(False)
        self.connect_btn.setStyleSheet(
            "QPushButton{background:#89b4fa;color:#1e1e2e;border-radius:8px;"
            "font-weight:bold;font-size:15px;}"
            "QPushButton:hover{background:#b4d0ff;}"
        )
        self.connect_btn.clicked.connect(self._open_session)
        layout.addWidget(self.connect_btn)

        # Нижние кнопки управления списком
        bottom = QHBoxLayout()
        add_btn = self._small_btn("+ Добавить")
        add_btn.clicked.connect(self._add_device)
        edit_btn = self._small_btn("Редактировать")
        edit_btn.clicked.connect(self._edit_device)
        del_btn = self._small_btn("Удалить")
        del_btn.clicked.connect(self._delete_device)
        bottom.addWidget(add_btn)
        bottom.addWidget(edit_btn)
        bottom.addWidget(del_btn)
        bottom.addStretch()
        layout.addLayout(bottom)

    def _small_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setStyleSheet(
            "QPushButton{background:#313244;color:#cdd6f4;border:1px solid #45475a;"
            "border-radius:6px;font-size:13px;padding:0 12px;}"
            "QPushButton:hover{background:#45475a;}"
        )
        return btn

    def _refresh_list(self):
        self.list_widget.clear()
        for device in self.devices:
            item = QListWidgetItem(self.list_widget)
            widget = DeviceItem(device)
            item.setSizeHint(QSize(0, 62))
            self.list_widget.setItemWidget(item, widget)

    def _on_selection(self):
        row = self.list_widget.currentRow()
        self._selected_index = row if row >= 0 else None
        self.connect_btn.setVisible(self._selected_index is not None)
        if self._selected_index is not None:
            dev = self.devices[self._selected_index]
            self.connect_btn.setText(f"Подключиться к {dev['name']}")

    def _open_session(self):
        if self._selected_index is None:
            return
        device = self.devices[self._selected_index]
        from session_window import SessionWindow
        win = SessionWindow(device, parent=None)
        win.show()
        # Сохраняем ссылку чтобы окно не удалилось
        if not hasattr(self, "_sessions"):
            self._sessions = []
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
            self, "Удалить", f"Удалить устройство «{name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.devices[self._selected_index]
            save_devices(self.devices)
            self._selected_index = None
            self.connect_btn.setVisible(False)
            self._refresh_list()
