@echo off
echo Установка зависимостей...
pip install PyQt6 websockets --quiet

echo Запуск контроллера...
python main.py
pause
