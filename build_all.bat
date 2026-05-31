@echo off
echo ========================================
echo  Сборка агента (windows32.exe)
echo ========================================

cd agent

:: Генерируем TLS-сертификат если его нет
if not exist cert.pem (
    echo [*] Генерация TLS сертификата...
    python tls_gen.py
)

:: Устанавливаем зависимости
echo [*] Установка зависимостей агента...
pip install -r requirements.txt --quiet

:: Собираем
echo [*] Сборка агента...
pyinstaller build.spec --noconfirm --distpath ..\dist\agent

if errorlevel 1 (
    echo [!] Ошибка сборки агента
    pause
    exit /b 1
)

echo [+] Агент собран: dist\agent\windows32.exe

echo.
echo ========================================
echo  Сборка контроллера (test.exe)
echo ========================================

cd ..\controller

echo [*] Установка зависимостей контроллера...
pip install -r requirements.txt --quiet

echo [*] Сборка контроллера...
pyinstaller build.spec --noconfirm --distpath ..\dist\controller

if errorlevel 1 (
    echo [!] Ошибка сборки контроллера
    pause
    exit /b 1
)

echo [+] Контроллер собран: dist\controller\test.exe

cd ..

echo.
echo ========================================
echo  Готово!
echo ========================================
echo  Агент:       dist\agent\windows32.exe
echo  Контроллер:  dist\controller\test.exe
echo.
echo  Установка агента на удалённом ПК:
echo    windows32.exe --install
echo ========================================
pause
