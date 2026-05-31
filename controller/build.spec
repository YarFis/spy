# Сборка контроллера в test.exe
# Запуск: pyinstaller build.spec --noconfirm

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

hidden = (
    collect_submodules("PyQt6") +
    collect_submodules("websockets") +
    ["ssl", "hashlib", "uuid",
     "viewer", "connection", "device_list", "session_window",
     "file_panel", "clipboard_widget"]
)

datas = collect_data_files("PyQt6")

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "matplotlib", "numpy"],
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
    name="test",             # имя .exe контроллера
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=["Qt6*.dll"],  # Qt DLL не жмём — ломается
    console=False,
    uac_admin=False,
    icon=None,
)
