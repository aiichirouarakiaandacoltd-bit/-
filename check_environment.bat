@echo off
chcp 65001 >nul
echo ============================================================
echo  環境チェック - 日本が誇る皇室物語 動画製作システム
echo ============================================================
echo.

echo [1/5] Python...
python --version 2>nul
if errorlevel 1 (
    echo   NG: Pythonが見つかりません
) else (
    echo   OK
)
echo.

echo [2/5] FFmpeg...
ffmpeg -version 2>nul | findstr "ffmpeg version" >nul
if errorlevel 1 (
    echo   NG: FFmpegが見つかりません
) else (
    echo   OK
)
echo.

echo [3/5] ffprobe...
ffprobe -version 2>nul | findstr "ffprobe version" >nul
if errorlevel 1 (
    echo   NG: ffprobeが見つかりません
) else (
    echo   OK
)
echo.

echo [4/5] VOICEVOX (localhost:50021)...
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:50021/speakers 2>nul | findstr "200" >nul
if errorlevel 1 (
    echo   NG: VOICEVOXが応答しません
    echo   VOICEVOXを起動してから再実行してください
) else (
    echo   OK: VOICEVOX応答確認
)
echo.

echo [5/5] BGMファイル...
if exist "assets\bgm\UNL1337.wav" (
    echo   OK: assets\bgm\UNL1337.wav
) else (
    echo   NG: assets\bgm\UNL1337.wav が見つかりません
)
echo.

echo ============================================================
echo  Pythonパッケージチェック
echo ============================================================
python -c "import requests; print('  OK: requests')" 2>nul || echo   NG: requests
python -c "from PIL import Image; print('  OK: Pillow')" 2>nul || echo   NG: Pillow
echo.

echo ============================================================
echo  チェック完了
echo ============================================================
pause
