#!/bin/bash
echo "========================================"
echo " Установка зависимостей"
echo "========================================"
pip3 install pyinstaller PyQt6 websockets --quiet

echo ""
echo "========================================"
echo " Сборка контроллера > test.app"
echo "========================================"

pyinstaller --noconfirm --onefile --windowed \
    --name test \
    --hidden-import PyQt6 \
    --hidden-import PyQt6.QtWidgets \
    --hidden-import PyQt6.QtCore \
    --hidden-import PyQt6.QtGui \
    --hidden-import websockets \
    --hidden-import websockets.legacy \
    --hidden-import websockets.legacy.client \
    --hidden-import ssl \
    main.py

mv dist/test ../test_mac

echo ""
echo "========================================"
echo " Готово! > test_mac"
echo "========================================"
