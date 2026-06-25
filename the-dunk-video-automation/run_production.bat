@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   ザ・ダンク 本番モード実行
echo ============================================
echo.
echo 本番モードを開始します。
echo 事前にVOICEVOXを起動し、素材を配置してください。
echo.
set /p CONFIRM=実行しますか？ (Y/N):
if /i not "%CONFIRM%"=="Y" (
    echo キャンセルしました。
    pause
    exit /b
)
echo.
cd /d "%~dp0"
python main.py --mode production
echo.
if errorlevel 1 (
    echo.
    echo エラーが発生しました。
    echo check_environment.bat で環境を確認してください。
)
echo.
pause
