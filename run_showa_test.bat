@echo off
chcp 65001 > nul
setlocal

cd /d "%~dp0"

echo ============================================================
echo   昭和・平成 なぜそうだったのか
echo   動画自動生成システム — 本番テスト実行
echo ============================================================
echo.
echo   チャンネル : showa_heisei
echo   テーマ     : なぜ家族全員で1台のテレビを見ていたのか
echo   話速       : 0.92 (青山龍星)
echo   BGM        : assets\bgm\showa_heisei\ から自動選択
echo.
echo   ※ 実行前に check_environment.bat で環境を確認してください。
echo   ※ VOICEVOX を起動してから実行してください。
echo   ※ assets\bgm\showa_heisei\ に権利確認済みBGMを配置してください。
echo.

:: 環境確認
python --version > nul 2>&1
if %errorlevel% NEQ 0 (
    echo FAIL: Python が見つかりません。インストールしてください。
    pause
    exit /b 1
)

python -c "import requests; requests.get('http://127.0.0.1:50021/version', timeout=2)" > nul 2>&1
if %errorlevel% NEQ 0 (
    echo.
    echo FAIL: VOICEVOX に接続できません。
    echo       VOICEVOX を起動してから再実行してください。
    echo       確認URL: http://127.0.0.1:50021
    echo.
    echo テーマだけ確認する場合 (--dry-run):
    echo   python create_video.py --channel showa_heisei --theme "なぜ家族全員で1台のテレビを見ていたのか" --dry-run
    pause
    exit /b 1
)

echo VOICEVOX: 接続確認
echo.

:: 本番実行
echo [実行] python create_video.py --channel showa_heisei --theme "なぜ家族全員で1台のテレビを見ていたのか" --voicevox-speed 0.92
echo.

python create_video.py ^
  --channel showa_heisei ^
  --theme "なぜ家族全員で1台のテレビを見ていたのか" ^
  --voicevox-speed 0.92

if %errorlevel% NEQ 0 (
    echo.
    echo ============================================================
    echo   FAIL: 動画生成に失敗しました。
    echo   上記のエラーメッセージを確認してください。
    echo   ログ: logs\ フォルダを確認してください。
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo   完了しました。videos\ フォルダを確認してください。
    echo   output.mp4 を最初から最後まで視聴して確認してください。
    echo ============================================================
)

echo.
pause
endlocal
