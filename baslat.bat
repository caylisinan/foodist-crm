@echo off
chcp 65001 >nul
title Foodist Hosted Buyer CRM

cd /d %~dp0

REM Bazi kurumsal bilgisayarlarda Windows'un varsayilan Temp klasorunde
REM program calistirma guvenlik yazilimi tarafindan engellenebiliyor.
REM Bunu asmak icin gecici dosyalari bu klasorun icine yonlendiriyoruz.
if not exist ".tmp" mkdir ".tmp"
set TEMP=%~dp0.tmp
set TMP=%~dp0.tmp

echo ============================================================
echo   FOODIST HOSTED BUYER CRM baslatiliyor...
echo   Bu pencereyi kapatmayin.
echo ============================================================
echo.

echo [1/4] Python kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo HATA: Python bulunamadi.
    echo Once https://python.org adresinden Python kurun.
    echo Kurulum ekraninda "Add python.exe to PATH" kutusunu isaretleyin.
    echo.
    pause
    exit /b 1
)

echo [2/4] pip kontrol ediliyor...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo       pip bulunamadi, kuruluyor...
    python -m ensurepip --upgrade
    if errorlevel 1 (
        echo.
        echo ============================================================
        echo   HATA: pip kurulamadi.
        echo.
        echo   Bu, bilgisayarinizdaki bir guvenlik/antivirus yazilimi
        echo   Windows'un gecici dosya klasorunde program calistirilmasini
        echo   engelledigi icin oluyor olabilir. Bu genelde IT/BT
        echo   departmani tarafindan yonetilen sirket bilgisayarlarinda
        echo   goruluyor.
        echo.
        echo   Onerilen: Bu programi kisisel bilgisayarinizda deneyin,
        echo   veya IT departmanindan bu klasor icin ^(ve Python'un
        echo   calistigi klasor icin^) bir istisna/izin istemenizi
        echo   rica ederiz.
        echo ============================================================
        echo.
        pause
        exit /b 1
    )
)

echo [3/4] Gerekli kutuphaneler kontrol ediliyor / kuruluyor...
echo       (Ilk calistirmada bu adim 2-5 dakika surebilir, lutfen bekleyin)
echo.

python -m pip install --no-cache-dir --disable-pip-version-check -q -r backend\requirements.txt
if errorlevel 1 (
    echo.
    echo Ilk deneme basarisiz oldu, tekrar deneniyor...
    timeout /t 3 >nul
    python -m pip install --no-cache-dir --disable-pip-version-check -q -r backend\requirements.txt
)

python -m pip install --no-cache-dir --disable-pip-version-check -q -r frontend\requirements.txt
if errorlevel 1 (
    echo.
    echo Ilk deneme basarisiz oldu, tekrar deneniyor...
    timeout /t 3 >nul
    python -m pip install --no-cache-dir --disable-pip-version-check -q -r frontend\requirements.txt
)

echo.
echo [4/4] Program aciliyor...
echo.

python app_launcher.py
set APP_EXIT_CODE=%errorlevel%

echo.
echo ============================================================
if "%APP_EXIT_CODE%"=="0" (
    echo   Program kapandi ^(normal cikis^).
) else (
    echo   Program bir hatayla kapandi ^(kod: %APP_EXIT_CODE%^).
    echo   Yukaridaki yazilarin ekran goruntusunu alip destek icin gonderin.
)
echo ============================================================
echo.
echo Bu pencereyi kapatmak icin bir tusa basin...
pause >nul

