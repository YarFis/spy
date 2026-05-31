import json
import asyncio
import base64
import ssl
import websockets
from PyQt6.QtCore import pyqtSignal, QThread


class ConnectionWorker(QThread):
    frame_received = pyqtSignal(bytes)
    message_received = pyqtSignal(dict)   # все сообщения кроме frame
    connected = pyqtSignal(dict)
    disconnected = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, host: str, port: int, password: str, use_tls: bool = True):
        super().__init__()
        self.host = host
        self.port = port
        self.password = password
        self.use_tls = use_tls
        self._ws = None
        self._loop = None
        self._input_queue: asyncio.Queue | None = None
        self._running = False

    def run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._connect())

    def _make_ssl(self) -> ssl.SSLContext | None:
        if not self.use_tls:
            return None
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    async def _connect(self):
        ssl_ctx = self._make_ssl()
        proto = "wss" if ssl_ctx else "ws"
        uri = f"{proto}://{self.host}:{self.port}"
        self._input_queue = asyncio.Queue()
        self._running = True

        try:
            async with websockets.connect(
                uri, ssl=ssl_ctx, ping_interval=20, ping_timeout=10
            ) as ws:
                self._ws = ws

                await ws.send(json.dumps({"password": self.password}))
                resp = json.loads(await ws.recv())

                if not resp.get("ok"):
                    reason = resp.get("reason", "неверный пароль")
                    self.error.emit(f"Ошибка авторизации: {reason}")
                    return

                self.connected.emit(resp)

                await asyncio.gather(
                    self._receive(ws),
                    self._send_inputs(ws),
                )

        except (OSError, websockets.exceptions.WebSocketException) as e:
            self.error.emit(str(e))
        finally:
            self._ws = None
            self._running = False
            self.disconnected.emit("Соединение закрыто")

    async def _receive(self, ws):
        async for message in ws:
            try:
                msg = json.loads(message)
                if msg.get("type") == "frame":
                    frame_bytes = base64.b64decode(msg["data"])
                    self.frame_received.emit(frame_bytes)
                else:
                    self.message_received.emit(msg)
            except (json.JSONDecodeError, KeyError):
                pass

    async def _send_inputs(self, ws):
        while self._running:
            try:
                event = await asyncio.wait_for(self._input_queue.get(), timeout=1.0)
                await ws.send(json.dumps(event))
            except asyncio.TimeoutError:
                continue
            except websockets.ConnectionClosed:
                break

    def send_event(self, event: dict):
        if self._input_queue and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._input_queue.put(event), self._loop
            )

    def disconnect(self):
        self._running = False
        if self._ws and self._loop:
            asyncio.run_coroutine_threadsafe(self._ws.close(), self._loop)
