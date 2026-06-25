@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

echo ============================================
echo   環境診断 - 昭和・平成動画自動化
echo   Windows実機未検証
echo ============================================
echo.

set ERRORS=0

REM --- Python検出 ---
echo [1/6] Python検出...
where python >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   OK: %%v
) else (
    where py >nul 2>&1
    if !ERRORLEVEL!==0 (
        for /f "tokens=*" %%v in ('py --version 2^>^&1') do echo   OK: %%v
    ) else (
        echo   FAIL: Python が見つかりません
        set /a ERRORS+=1
    )
)

REM --- FFmpeg検出 ---
echo [2/6] FFmpeg検出...
where ffmpeg >nul 2>&1
if %ERRORLEVEL%==0 (
    for /f "tokens=3" %%v in ('ffmpeg -version 2^>^&1 ^| findstr /B "ffmpeg version"') do echo   OK: ffmpeg %%v
) else (
    echo   FAIL: ffmpeg が見つかりません
    set /a ERRORS+=1
)

REM --- ffprobe検出 ---
echo [3/6] ffprobe検出...
where ffprobe >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   OK: ffprobe 検出
) else (
    echo   FAIL: ffprobe が見つかりません
    set /a ERRORS+=1
)

REM --- VOICEVOX接続 ---
echo [4/6] VOICEVOX接続確認...
curl -s -o nul -w "%%{http_code}" http://localhost:50021/speakers >nul 2>&1
if %ERRORLEVEL%==0 (
    echo   OK: VOICEVOX 応答あり
) else (
    echo   WARNING: VOICEVOX に接続できません（テストモードは続行可能）
)

REM --- 設定ファイル確認 ---
echo [5/6] 設定ファイル確認...
if exist "%~dp0config\settings.yaml" (
    echo   OK: config/settings.yaml
) else (
    echo   FAIL: config/settings.yaml が見つかりません
    set /a ERRORS+=1
)
if exist "%~dp0config\speakers.yaml" (
    echo   OK: config/speakers.yaml
) else (
    echo   FAIL: config/speakers.yaml が見つかりません
    set /a ERRORS+=1
)

REM --- BGM確認 ---
echo [6/6] BGM確認...
if exist "%~dp0assets\bgm\bgm_license.json" (
    echo   OK: BGMライセンスファイルあり
) else (
    echo   INFO: assets/bgm/bgm_license.json なし（本番モードにはBGM必須）
)

echo.
echo ============================================
if %ERRORS%==0 (
    echo   結果: 全チェック通過
    echo ============================================
    echo.
    echo プリフライトチェックも実行しますか？
    set /p RUN_PF="実行する場合は Y を入力: "
    if /i "!RUN_PF!"=="Y" (
        echo.
        python "%~dp0main.py" --preflight --mode test
    )
) else (
    echo   結果: %ERRORS% 件のエラー
    echo ============================================
)

echo.
echo 何かキーを押すと終了します。
pause >nul
exit /b %ERRORS%
