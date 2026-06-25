@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo ============================================
echo   テストモード実行
echo   TEST ONLY - 投稿不可 - 技術検証用
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

REM --- テーマ入力 ---
set "TOPIC=なぜ昔のテレビには布をかけていたのか"
echo デフォルトテーマ: %TOPIC%
set /p "USER_TOPIC=別テーマを入力（Enterでデフォルト）: "
if not "!USER_TOPIC!"=="" set "TOPIC=!USER_TOPIC!"

echo.
echo テーマ: !TOPIC!
echo モード: test（テスト）
echo 出力先: outputs\test\
echo.
echo ※テスト出力はTEST_ONLY_のプレフィックス付きです
echo ※テスト動画は投稿不可です
echo.

!PYTHON_CMD! "%~dp0main.py" --topic "!TOPIC!" --mode test
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE%==0 (
    echo テストモード正常完了
) else (
    echo テストモードがエラーで終了しました（コード: %EXIT_CODE%）
)

:END
echo.
echo 何かキーを押すと終了します。
pause >nul
exit /b %EXIT_CODE%
