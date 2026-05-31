# -*- coding: utf-8 -*-
"""
Запуск агента напрямую для теста — без установки службы.
Запускать от администратора:
    python run_test.py
"""
import asyncio
from server import AgentServer


async def main():
    print("=" * 40)
    print(" Агент запущен в режиме теста")
    print(" Порт: 8765")
    print(" TLS:  включён (если есть cert.pem)")
    print(" Ctrl+C для остановки")
    print("=" * 40)

    server = AgentServer(host="0.0.0.0", port=8765)
    await server.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Агент остановлен")
