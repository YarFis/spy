import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from device_list import DeviceListWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Test")
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet("QToolTip{background:#313244;color:#cdd6f4;border:1px solid #45475a;}")

    window = DeviceListWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
