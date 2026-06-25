@echo off
chcp 65001 >nul 2>&1
echo ============================================================
echo  Imperial Video Automation - 環境チェック
echo ============================================================
echo.

echo [1] Python確認...
python --version 2>nul
if errorlevel 1 (
    echo [FAIL] Pythonが見つかりません。Python 3.9以上をインストールしてください。
    goto :end
)

echo.
echo [2] FFmpeg確認...
ffmpeg -version 2>nul | findstr "ffmpeg version"
if errorlevel 1 (
    echo [FAIL] FFmpegが見つかりません。FFmpegをインストールしてPATHに追加してください。
    goto :end
)

echo.
echo [3] ffprobe確認...
ffprobe -version 2>nul | findstr "ffprobe version"
if errorlevel 1 (
    echo [FAIL] ffprobeが見つかりません。
    goto :end
)

echo.
echo [4] Pythonパッケージ確認...
pip install -r requirements.txt --quiet 2>nul

echo.
echo [5] BGMファイル確認...
if exist "assets\bgm\UNL1337.wav" (
    echo [OK] UNL1337.wav が見つかりました。
) else (
    echo [WARN] assets\bgm\UNL1337.wav が見つかりません。
    echo        本番モードにはBGMファイルが必要です。
)

echo.
echo [6] VOICEVOX確認...
curl -s --connect-timeout 3 http://localhost:50021/speakers >nul 2>&1
if errorlevel 1 (
    echo [WARN] VOICEVOXに接続できません。
    echo        本番モードにはVOICEVOXの起動が必要です。
) else (
    echo [OK] VOICEVOXに接続できました。
)

echo.
echo [7] 詳細プリフライト...
python main.py --preflight-only --test-mode
echo.

:end
echo.
echo ============================================================
echo  チェック完了
echo ============================================================
pause
