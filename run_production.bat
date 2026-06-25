@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo ============================================
echo   本番モード実行
echo   昭和・平成 なぜそうだったのか
echo   Windows実機未検証
echo ============================================
echo.

REM --- Python検出 ---
set PYTHON_CMD=
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    set PYTHON_CMD=python
) else (
    where py >nul 2>&1
    if !ERRORLEVEL!==0 (
        set PYTHON_CMD=py
    ) else (
        echo エラー: Python が見つかりません。
        echo Python 3.11以上をインストールしてください。
        goto :END
    )
)

REM --- FFmpeg検出 ---
where ffmpeg >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo エラー: FFmpeg が見つかりません。
    echo FFmpegをインストールしPATHに追加してください。
    goto :END
)

REM --- VOICEVOX接続確認 ---
echo VOICEVOX接続確認中...
curl -s -o nul -w "%%{http_code}" http://localhost:50021/speakers >nul 2>&1
if not %ERRORLEVEL%==0 (
    echo エラー: VOICEVOXに接続できません。
    echo VOICEVOXを起動してから再実行してください。
    echo 本番モードではVOICEVOXが必須です。
    goto :END
)
echo   VOICEVOX: 接続OK

REM --- BGM確認 ---
if not exist "%~dp0assets\bgm\bgm_license.json" (
    echo エラー: BGMライセンスファイルが見つかりません。
    echo assets\bgm\ に権利確認済みBGMとbgm_license.jsonを配置してください。
    echo 本番モードでは権利確認済みBGMが必須です。
    goto :END
)
echo   BGM: ライセンスファイル確認OK

REM --- テーマ入力 ---
set /p "TOPIC=テーマを入力してください: "
if "!TOPIC!"=="" (
    echo エラー: テーマが入力されていません。
    goto :END
)

echo.
echo テーマ: !TOPIC!
echo モード: production（本番）
echo 出力先: outputs\production\
echo.
echo 本番モード開始...
echo.

!PYTHON_CMD! "%~dp0main.py" --topic "!TOPIC!" --mode production
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE%==0 (
    echo 本番モード正常完了
    echo 出力フォルダを確認してください: outputs\production\
) else (
    echo 本番モードがエラーで終了しました（コード: %EXIT_CODE%）
)

:END
echo.
echo 何かキーを押すと終了します。
pause >nul
exit /b %EXIT_CODE%
