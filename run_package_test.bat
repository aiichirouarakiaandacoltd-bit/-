@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1
echo ============================================================
echo  Imperial Video Automation - 制作パッケージ生成テスト
echo ============================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "EXIT_CODE=0"
set "THEME=なぜ昔のテレビには布をかけていたのか"

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

REM 必要フォルダ確認
if not exist "%SCRIPT_DIR%src" (
    echo [FAIL] srcフォルダが見つかりません。
    set "EXIT_CODE=1"
    goto :end
)
echo [OK] srcフォルダ確認

if not exist "%SCRIPT_DIR%config.py" (
    echo [FAIL] config.pyが見つかりません。
    set "EXIT_CODE=1"
    goto :end
)
echo [OK] config.py確認

echo.
echo ============================================================
echo  [1/2] テストモードで実行
echo ============================================================
echo.

%PY_CMD% "%SCRIPT_DIR%main.py" generate --test --theme "%THEME%"
if errorlevel 1 (
    echo.
    echo [FAIL] テストモードで失敗しました。
    set "EXIT_CODE=1"
    goto :show_results
)
echo [OK] テストモード完了

echo.
echo ============================================================
echo  [2/2] プロダクションモードで実行
echo ============================================================
echo.

%PY_CMD% "%SCRIPT_DIR%main.py" generate --production --theme "%THEME%"
if errorlevel 1 (
    echo.
    echo [FAIL] プロダクションモードで失敗しました。
    set "EXIT_CODE=1"
    goto :show_results
)
echo [OK] プロダクションモード完了

:show_results
echo.
echo ============================================================
echo  出力結果
echo ============================================================
echo.
echo 出力フォルダ:
dir /b "%SCRIPT_DIR%output\packages\" 2>nul
echo.

REM 最新のmetadata.jsonを探して表示
for /f "delims=" %%d in ('dir /b /ad /o-d "%SCRIPT_DIR%output\packages\" 2^>nul') do (
    if exist "%SCRIPT_DIR%output\packages\%%d\metadata.json" (
        echo 最新パッケージ: %%d
        echo.
        echo metadata.json:
        type "%SCRIPT_DIR%output\packages\%%d\metadata.json"
        echo.
        goto :end
    )
)

:end
echo.
if %EXIT_CODE% neq 0 (
    echo [FAIL] テストに失敗しました。上記のログを確認してください。
) else (
    echo [OK] テスト完了。output\packages フォルダを確認してください。
)
echo.
echo 注意: Windows実機未検証 - 問題があれば報告してください。
pause
exit /b %EXIT_CODE%
