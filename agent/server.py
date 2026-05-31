import asyncio
import json
import base64
import ssl
import hashlib
import pathlib
import websockets
from screen import ScreenCapture
from input import InputHandler, InputBlocker
from filetransfer import FileReceiver, FileSender
from clipboard import get_clipboard, set_clipboard

PASSWORD_HASH = hashlib.sha256(b"changeme").hexdigest()  # << СМЕНИ ПЕРЕД СБОРКОЙ

CERT_FILE = pathlib.Path(__file__).parent / "cert.pem"
KEY_FILE  = pathlib.Path(__file__).parent / "key.pem"


def _make_ssl_context() -> ssl.SSLContext | None:
    if not CERT_FILE.exists() or not KEY_FILE.exists():
        return None
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(CERT_FILE), str(KEY_FILE))
    return ctx


class AgentServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.screen = ScreenCapture(quality=60, scale=0.8)
        self.input_handler = InputHandler()
        self.blocker = InputBlocker()
        self.receiver = FileReceiver()
        self.active_session: websockets.WebSocketServerProtocol | None = None
        self.ssl_ctx = _make_ssl_context()
        self._last_clipboard: str | None = None

    async def handle(self, ws: websockets.WebSocketServerProtocol):
        try:
            auth_msg = await asyncio.wait_for(ws.recv(), timeout=10)
            auth = json.loads(auth_msg)
            incoming_hash = hashlib.sha256(auth.get("password", "").encode()).hexdigest()
            if incoming_hash != PASSWORD_HASH:
                await ws.send(json.dumps({"type": "auth", "ok": False}))
                return
        except (asyncio.TimeoutError, json.JSONDecodeError):
            return

        if self.active_session is not None:
            await ws.send(json.dumps({"type": "auth", "ok": False, "reason": "busy"}))
            return

        self.active_session = ws
        # Блокировка физического ввода — только по команде take_control
        await ws.send(json.dumps({
            "type": "auth",
            "ok": True,
            "tls": self.ssl_ctx is not None,
            "monitors": self.screen.get_monitors(),
        }))

        stream_task = asyncio.create_task(self._stream_screen(ws))
        clipboard_task = asyncio.create_task(self._watch_clipboard(ws))

        try:
            async for message in ws:
                try:
                    event = json.loads(message)
                    await self._dispatch(ws, event)
                except json.JSONDecodeError:
                    pass
        except websockets.ConnectionClosed:
            pass
        finally:
            stream_task.cancel()
            clipboard_task.cancel()
            self.blocker.unblock()  # всегда разблокируем при отключении
            self.active_session = None

    async def _dispatch(self, ws, event: dict):
        t = event.get("type")

        # Администратор берёт управление — блокируем физический ввод
        if t == "take_control":
            self.blocker.block()

        # Администратор отдаёт управление — разблокируем
        elif t == "release_control":
            self.blocker.unblock()

        # Ввод мыши / клавиатуры
        elif t in ("mouse_move", "mouse_click", "mouse_down", "mouse_up",
                   "scroll", "key_press", "key_down", "key_up", "type_text"):
            self.input_handler.handle(event)

        # Буфер обмена: контроллер → агент
        elif t == "clipboard_set":
            set_clipboard(event.get("text", ""))

        # Контроллер запрашивает текущий буфер агента
        elif t == "clipboard_get":
            text = get_clipboard() or ""
            await ws.send(json.dumps({"type": "clipboard_data", "text": text}))

        # Приём файла от контроллера (upload на удалённый ПК)
        elif t == "file_begin":
            resp = self.receiver.begin(
                event["id"], event["dest"], event["size"], event["chunks"]
            )
            await ws.send(json.dumps(resp))

        elif t == "file_chunk":
            resp = self.receiver.chunk(event["id"], event["index"], event["data"])
            await ws.send(json.dumps(resp))

        elif t == "file_finish":
            resp = self.receiver.finish(event["id"], event["md5"])
            await ws.send(json.dumps(resp))

        # Отправка файла контроллеру (download с удалённого ПК)
        elif t == "file_download":
            await self._send_file(ws, event["path"])

        # Список файлов/папок на удалённом ПК
        elif t == "dir_list":
            await ws.send(json.dumps(self._list_dir(event.get("path", "C:\\"))))

    async def _send_file(self, ws, src_path: str):
        info = FileSender.prepare(src_path)
        if info.get("type") == "file_error":
            await ws.send(json.dumps(info))
            return
        await ws.send(json.dumps(info))
        for index, data_b64 in FileSender.read_chunks(src_path):
            await ws.send(json.dumps({
                "type": "file_chunk",
                "path": src_path,
                "index": index,
                "data": data_b64,
            }))
            await asyncio.sleep(0)  # отдаём управление event loop'у

    def _list_dir(self, path: str) -> dict:
        import os
        try:
            entries = []
            for entry in os.scandir(path):
                entries.append({
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else 0,
                })
            return {"type": "dir_list", "path": path, "entries": entries}
        except PermissionError:
            return {"type": "dir_list", "path": path, "entries": [], "error": "permission_denied"}
        except FileNotFoundError:
            return {"type": "dir_list", "path": path, "entries": [], "error": "not_found"}

    async def _stream_screen(self, ws, fps: int = 20):
        interval = 1 / fps
        while True:
            try:
                frame = self.screen.capture()
                await ws.send(json.dumps({
                    "type": "frame",
                    "data": base64.b64encode(frame).decode()
                }))
                await asyncio.sleep(interval)
            except Exception:
                break

    async def _watch_clipboard(self, ws):
        """Следит за буфером обмена агента и уведомляет контроллер при изменении."""
        while True:
            try:
                current = get_clipboard()
                if current and current != self._last_clipboard:
                    self._last_clipboard = current
                    await ws.send(json.dumps({
                        "type": "clipboard_changed",
                        "text": current
                    }))
                await asyncio.sleep(1)
            except Exception:
                break

    async def start(self):
        async with websockets.serve(
            self.handle, self.host, self.port, ssl=self.ssl_ctx
        ):
            await asyncio.Future()


def run():
    asyncio.run(AgentServer().start())
