@echo off
chcp 65001 >nul 2>&1
echo ============================================================
echo  Imperial Video Automation - 動画生成
echo ============================================================
echo.

echo 事前確認を実行中...
echo.

REM VOICEVOX確認
curl -s --connect-timeout 3 http://localhost:50021/speakers >nul 2>&1
if errorlevel 1 (
    echo [FAIL] VOICEVOXに接続できません。
    echo        VOICEVOXを起動してから再実行してください。
    echo.
    pause
    exit /b 1
)
echo [OK] VOICEVOX接続確認

REM BGM確認
if not exist "assets\bgm\UNL1337.wav" (
    echo [FAIL] assets\bgm\UNL1337.wav が見つかりません。
    echo        BGMファイルを配置してから再実行してください。
    echo.
    pause
    exit /b 1
)
echo [OK] BGMファイル確認

echo.
echo ============================================================
echo  本番モードで動画生成を開始します
echo ============================================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [FAIL] 動画生成に失敗しました。
    echo        logs フォルダのログを確認してください。
) else (
    echo.
    echo [OK] 動画生成が完了しました。
    echo      output フォルダを確認してください。
)

echo.
pause
