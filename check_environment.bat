@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
echo ============================================================
echo  Imperial Video Automation - 環境チェック
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"

echo [1] Python確認...
where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    python --version 2>&1
    goto :py_found
)
where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py"
    py --version 2>&1
    goto :py_found
)
echo [FAIL] pythonまたはpyが見つかりません。Python 3.9以上をインストールしてください。
goto :end

:py_found
echo [OK] Python検出: %PY_CMD%

echo.
echo [2] FFmpeg確認...
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [FAIL] FFmpegが見つかりません。FFmpegをインストールしてPATHに追加してください。
    goto :end
)
ffmpeg -version 2>&1 | findstr "ffmpeg version"
echo [OK] FFmpeg検出

echo.
echo [3] ffprobe確認...
where ffprobe >nul 2>&1
if errorlevel 1 (
    echo [FAIL] ffprobeが見つかりません。
    goto :end
)
ffprobe -version 2>&1 | findstr "ffprobe version"
echo [OK] ffprobe検出

echo.
echo [4] Pythonパッケージ確認...
%PY_CMD% -m pip install -r "%SCRIPT_DIR%requirements.txt" --quiet 2>nul
if errorlevel 1 (
    echo [WARN] パッケージインストールに問題がありました。
) else (
    echo [OK] パッケージインストール完了
)

echo.
echo [5] BGMファイル確認...
if exist "%SCRIPT_DIR%assets\bgm\UNL1337.wav" (
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
%PY_CMD% "%SCRIPT_DIR%main.py" --preflight-only --test-mode
echo.

:end
echo.
echo ============================================================
echo  チェック完了
echo ============================================================
echo.
echo 注意: Windows実機未検証 - 問題があれば報告してください。
pause
exit /b %errorlevel%
