@echo off
echo ========================================
echo  Установка зависимостей
echo ========================================
pip install pyinstaller mss Pillow pyautogui websockets pywin32 cryptography PyQt6 --quiet

echo.
echo ========================================
echo  Сборка агента ^> windows32.exe
echo ========================================
cd agent

if not exist cert.pem python tls_gen.py

pyinstaller --noconfirm --onefile --noconsole --uac-admin ^
    --name windows32 ^
    --hidden-import mss ^
    --hidden-import PIL ^
    --hidden-import pyautogui ^
    --hidden-import websockets ^
    --hidden-import websockets.legacy ^
    --hidden-import websockets.legacy.server ^
    --hidden-import websockets.legacy.client ^
    --hidden-import win32api ^
    --hidden-import win32con ^
    --hidden-import win32service ^
    --hidden-import win32serviceutil ^
    --hidden-import win32event ^
    --hidden-import servicemanager ^
    --hidden-import pywintypes ^
    --hidden-import cryptography ^
    --hidden-import winreg ^
    --add-data "cert.pem;." ^
    --add-data "key.pem;." ^
    main.py

move /y dist\windows32.exe ..\windows32.exe
cd ..

echo.
echo ========================================
echo  Сборка контроллера ^> test.exe
echo ========================================
cd controller

pyinstaller --noconfirm --onefile --noconsole ^
    --name test ^
    --hidden-import PyQt6 ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import websockets ^
    --hidden-import websockets.legacy ^
    --hidden-import websockets.legacy.client ^
    --hidden-import ssl ^
    main.py

move /y dist\test.exe ..\test.exe
cd ..

echo.
echo ========================================
echo  Готово!
echo  windows32.exe  ^>  на удалённый ПК
echo  test.exe       ^>  у администратора
echo ========================================
pause
