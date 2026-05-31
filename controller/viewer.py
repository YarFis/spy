from PyQt6.QtWidgets import QWidget, QLabel, QSizePolicy
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QPixmap, QImage, QCursor, QKeyEvent, QMouseEvent, QWheelEvent
import io


class ScreenViewer(QWidget):
    """Отображает экран удалённого ПК и перехватывает ввод."""

    mouse_event = pyqtSignal(dict)
    key_event = pyqtSignal(dict)

    # Кнопки Qt -> строки pyautogui
    BUTTON_MAP = {
        Qt.MouseButton.LeftButton: "left",
        Qt.MouseButton.RightButton: "right",
        Qt.MouseButton.MiddleButton: "middle",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.remote_w = 1920
        self.remote_h = 1080
        self._pixmap = QPixmap()

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.BlankCursor)

    def update_frame(self, jpeg_bytes: bytes):
        img = QImage.fromData(jpeg_bytes, "JPEG")
        if not img.isNull():
            self._pixmap = QPixmap.fromImage(img)
            self.remote_w = img.width()
            self.remote_h = img.height()
            self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        x = (self.width() - scaled.width()) // 2
        y = (self.height() - scaled.height()) // 2
        painter.drawPixmap(x, y, scaled)

    def _to_remote(self, pos: QPoint) -> tuple[int, int]:
        """Пересчитывает координаты виджета в координаты удалённого экрана."""
        scaled_w = self.width()
        scaled_h = int(self.remote_h * scaled_w / self.remote_w)
        if scaled_h > self.height():
            scaled_h = self.height()
            scaled_w = int(self.remote_w * scaled_h / self.remote_h)

        off_x = (self.width() - scaled_w) // 2
        off_y = (self.height() - scaled_h) // 2

        rx = int((pos.x() - off_x) / scaled_w * self.remote_w)
        ry = int((pos.y() - off_y) / scaled_h * self.remote_h)
        return max(0, rx), max(0, ry)

    def mouseMoveEvent(self, event: QMouseEvent):
        x, y = self._to_remote(event.pos())
        self.mouse_event.emit({"type": "mouse_move", "x": x, "y": y})

    def mousePressEvent(self, event: QMouseEvent):
        x, y = self._to_remote(event.pos())
        btn = self.BUTTON_MAP.get(event.button(), "left")
        self.mouse_event.emit({"type": "mouse_down", "x": x, "y": y, "button": btn})

    def mouseReleaseEvent(self, event: QMouseEvent):
        x, y = self._to_remote(event.pos())
        btn = self.BUTTON_MAP.get(event.button(), "left")
        self.mouse_event.emit({"type": "mouse_up", "x": x, "y": y, "button": btn})

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        x, y = self._to_remote(event.pos())
        btn = self.BUTTON_MAP.get(event.button(), "left")
        self.mouse_event.emit({"type": "mouse_click", "x": x, "y": y, "button": btn, "double": True})

    def wheelEvent(self, event: QWheelEvent):
        x, y = self._to_remote(event.position().toPoint())
        dy = event.angleDelta().y() // 120
        self.mouse_event.emit({"type": "scroll", "x": x, "y": y, "dy": dy})

    def keyPressEvent(self, event: QKeyEvent):
        key = self._qt_key_to_pyautogui(event)
        if key:
            self.key_event.emit({"type": "key_down", "key": key})

    def keyReleaseEvent(self, event: QKeyEvent):
        key = self._qt_key_to_pyautogui(event)
        if key:
            self.key_event.emit({"type": "key_up", "key": key})

    def _qt_key_to_pyautogui(self, event: QKeyEvent) -> str | None:
        text = event.text()
        if text and text.isprintable():
            return text

        from PyQt6.QtCore import Qt as Q
        KEY_MAP = {
            Q.Key.Key_Return: "enter", Q.Key.Key_Enter: "enter",
            Q.Key.Key_Backspace: "backspace", Q.Key.Key_Delete: "delete",
            Q.Key.Key_Tab: "tab", Q.Key.Key_Escape: "escape",
            Q.Key.Key_Space: "space",
            Q.Key.Key_Up: "up", Q.Key.Key_Down: "down",
            Q.Key.Key_Left: "left", Q.Key.Key_Right: "right",
            Q.Key.Key_Home: "home", Q.Key.Key_End: "end",
            Q.Key.Key_PageUp: "pageup", Q.Key.Key_PageDown: "pagedown",
            Q.Key.Key_F1: "f1", Q.Key.Key_F2: "f2", Q.Key.Key_F3: "f3",
            Q.Key.Key_F4: "f4", Q.Key.Key_F5: "f5", Q.Key.Key_F6: "f6",
            Q.Key.Key_F7: "f7", Q.Key.Key_F8: "f8", Q.Key.Key_F9: "f9",
            Q.Key.Key_F10: "f10", Q.Key.Key_F11: "f11", Q.Key.Key_F12: "f12",
            Q.Key.Key_Control: "ctrl", Q.Key.Key_Shift: "shift",
            Q.Key.Key_Alt: "alt", Q.Key.Key_Meta: "win",
        }
        return KEY_MAP.get(event.key())
