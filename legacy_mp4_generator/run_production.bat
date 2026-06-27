@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
echo ============================================================
echo  Imperial Video Automation - 本番動画生成
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"

REM Python検出
where python >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :py_ok
)
where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py"
    goto :py_ok
)
echo [FAIL] pythonまたはpyが見つかりません。
echo        Python 3.9以上をインストールしてください。
set "EXIT_CODE=1"
goto :end

:py_ok
echo [OK] Python検出: %PY_CMD%

REM FFmpeg検出
where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo [FAIL] FFmpegが見つかりません。
    set "EXIT_CODE=1"
    goto :end
)
echo [OK] FFmpeg検出

REM VOICEVOX確認
echo.
echo VOICEVOX接続確認中...
curl -s --connect-timeout 3 http://localhost:50021/speakers >nul 2>&1
if errorlevel 1 (
    echo [FAIL] VOICEVOXに接続できません。
    echo        VOICEVOXを起動してから再実行してください。
    set "EXIT_CODE=1"
    goto :end
)
echo [OK] VOICEVOX接続確認

REM BGM確認
if not exist "%SCRIPT_DIR%assets\bgm\UNL1337.wav" (
    echo [FAIL] assets\bgm\UNL1337.wav が見つかりません。
    echo        BGMファイルを配置してから再実行してください。
    set "EXIT_CODE=1"
    goto :end
)
echo [OK] BGMファイル確認

echo.
echo ============================================================
echo  本番モードで動画生成を開始します
echo  ※ テスト出力と本番出力は別フォルダに分離されています
echo ============================================================
echo.

%PY_CMD% "%SCRIPT_DIR%main.py"
set "EXIT_CODE=%errorlevel%"

if %EXIT_CODE% neq 0 (
    echo.
    echo [FAIL] 動画生成に失敗しました。
    echo        logs フォルダのログを確認してください。
) else (
    echo.
    echo [OK] 本番動画生成が完了しました。
    echo      output\long フォルダに長尺動画があります。
    echo      output\shorts フォルダにShorts動画があります。
    echo      ※ output\test はテスト用です。本番出力ではありません。
)

:end
echo.
echo 注意: Windows実機未検証 - 問題があれば報告してください。
pause
exit /b %EXIT_CODE%
