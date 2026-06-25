@echo off
chcp 65001 >nul 2>&1
if exist outputs\production (
    explorer outputs\production
) else (
    echo 出力フォルダが見つかりません。
    pause
)
