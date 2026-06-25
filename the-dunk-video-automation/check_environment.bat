@echo off
chcp 65001 >nul 2>&1
echo.
echo ============================================
echo   ザ・ダンク 環境チェック
echo ============================================
echo.

echo [1] Python確認...
python --version 2>nul
if errorlevel 1 (
    echo   ✗ Pythonが見つかりません
    echo   → https://www.python.org/ からインストールしてください
    echo.
) else (
    echo   ✓ Python OK
)

echo [2] FFmpeg確認...
ffmpeg -version 2>nul | findstr "ffmpeg version" >nul
if errorlevel 1 (
    echo   ✗ FFmpegが見つかりません
    echo   → https://ffmpeg.org/ からインストールしてください
    echo.
) else (
    echo   ✓ FFmpeg OK
)

echo [3] ffprobe確認...
ffprobe -version 2>nul | findstr "ffprobe version" >nul
if errorlevel 1 (
    echo   ✗ ffprobeが見つかりません
    echo   → FFmpegと一緒にインストールされます
    echo.
) else (
    echo   ✓ ffprobe OK
)

echo [4] VOICEVOX確認（話者: 青山龍星 / 速度: 0.95）...
curl -s --connect-timeout 3 http://localhost:50021/version >nul 2>&1
if errorlevel 1 (
    echo   ✗ VOICEVOXに接続できません
    echo   → VOICEVOXを起動してください
    echo.
) else (
    echo   ✓ VOICEVOX OK
)

echo [5] Pillowパッケージ確認...
python -c "import PIL" 2>nul
if errorlevel 1 (
    echo   ✗ Pillowが見つかりません
    echo   → pip install Pillow を実行してください
    echo.
) else (
    echo   ✓ Pillow OK
)

echo [6] 入力素材確認...
if exist "inputs\owned_videos\*.*" (
    echo   ✓ owned_videos に素材あり
) else (
    echo   △ owned_videos に素材がありません
    echo   → inputs\owned_videos\ にファイルを配置してください
)

echo.
echo ============================================
echo   チェック完了
echo ============================================
echo.
pause
