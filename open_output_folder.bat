@echo off
cd /d "%~dp0"
if exist "output\final.mp4" (
    explorer "output"
) else (
    echo output\final.mp4 がまだ生成されていません。
    echo 先に run_test.bat または run_production.bat を実行してください。
    pause
)
