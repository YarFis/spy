import mss
import mss.tools
from PIL import Image
import io
import base64


class ScreenCapture:
    def __init__(self, quality: int = 50, scale: float = 1.0):
        self.quality = quality
        self.scale = scale
        self.sct = mss.mss()

    def capture(self, monitor_index: int = 1) -> bytes:
        monitor = self.sct.monitors[monitor_index]
        screenshot = self.sct.grab(monitor)

        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        if self.scale != 1.0:
            new_size = (int(img.width * self.scale), int(img.height * self.scale))
            img = img.resize(new_size, Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=self.quality, optimize=True)
        return buf.getvalue()

    def capture_b64(self, monitor_index: int = 1) -> str:
        return base64.b64encode(self.capture(monitor_index)).decode()

    def get_monitors(self) -> list:
        return [
            {"index": i, "width": m["width"], "height": m["height"]}
            for i, m in enumerate(self.sct.monitors)
            if i > 0
        ]

    def close(self):
        self.sct.close()
