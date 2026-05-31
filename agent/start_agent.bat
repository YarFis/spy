@echo off
echo Установка зависимостей...
pip install mss Pillow pyautogui websockets pywin32 cryptography --quiet

echo Генерация сертификата...
python tls_gen.py

echo Запуск агента...
python run_test.py
pause
