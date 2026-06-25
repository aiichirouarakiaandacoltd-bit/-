@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   環境チェック - 昭和・平成動画自動化
echo ============================================
echo.
python main.py --preflight
echo.
echo 完了しました。何かキーを押してください。
pause >nul
