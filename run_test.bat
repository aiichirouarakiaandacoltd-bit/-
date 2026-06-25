@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   テストモード実行
echo ============================================
echo.
python main.py --topic "なぜ昔のテレビには布をかけていたのか" --mode test
echo.
echo 完了しました。何かキーを押してください。
pause >nul
