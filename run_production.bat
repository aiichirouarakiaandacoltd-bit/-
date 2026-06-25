@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   本番モード実行
echo ============================================
echo.
set /p TOPIC="テーマを入力してください: "
python main.py --topic "%TOPIC%" --mode production
echo.
echo 完了しました。何かキーを押してください。
pause >nul
