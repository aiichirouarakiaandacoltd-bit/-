@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   ザ・ダンク テストモード実行
echo   ※ この動画は投稿不可です
echo ============================================
echo.
cd /d "%~dp0"
python main.py --test-mode
echo.
if errorlevel 1 (
    echo.
    echo エラーが発生しました。
    echo check_environment.bat で環境を確認してください。
)
echo.
pause
