@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================================
echo   動画自動生成システム 環境診断
echo   check_environment.bat
echo ============================================================
echo.

set PASS_COUNT=0
set FAIL_COUNT=0
set WARN_COUNT=0

:: ------------------------------------------------------------------
:: ヘルパーマクロ的に変数使用
:: ------------------------------------------------------------------

echo [1/8] Python の確認...
python --version > nul 2>&1
if %errorlevel% NEQ 0 (
    echo   FAIL: Python が見つかりません
    echo   修正方法: https://www.python.org/ から Python 3.10 以上をインストールしてください
    set /a FAIL_COUNT+=1
) else (
    for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
    echo   PASS: !PY_VER!
    set /a PASS_COUNT+=1
)

echo.
echo [2/8] FFmpeg の確認...
ffmpeg -version > nul 2>&1
if %errorlevel% NEQ 0 (
    :: static_ffmpeg でインストール済みかチェック
    python -c "import static_ffmpeg; static_ffmpeg.add_paths(); import shutil; print(shutil.which('ffmpeg'))" > nul 2>&1
    if !errorlevel! EQU 0 (
        echo   PASS: FFmpeg (static_ffmpeg 経由)
        set /a PASS_COUNT+=1
    ) else (
        echo   FAIL: FFmpeg が見つかりません
        echo   修正方法: pip install static-ffmpeg  または  https://ffmpeg.org/download.html からインストール
        set /a FAIL_COUNT+=1
    )
) else (
    for /f "tokens=1-3" %%a in ('ffmpeg -version 2^>^&1 ^| findstr "ffmpeg version"') do (
        echo   PASS: %%a %%b %%c
    )
    set /a PASS_COUNT+=1
)

echo.
echo [3/8] VOICEVOX API の確認 (http://127.0.0.1:50021)...
python -c "import requests; r=requests.get('http://127.0.0.1:50021/version',timeout=3); print(r.text)" > nul 2>&1
if %errorlevel% NEQ 0 (
    echo   FAIL: VOICEVOX に接続できません
    echo   修正方法:
    echo     1. VOICEVOX をダウンロード: https://voicevox.hiroshiba.jp/
    echo     2. VOICEVOX アプリを起動してください
    echo     3. タスクトレイに常駐していることを確認してください
    set /a FAIL_COUNT+=1
) else (
    for /f "tokens=*" %%v in ('python -c "import requests; r=requests.get(\"http://127.0.0.1:50021/version\",timeout=3); print(r.text.strip())"') do set VV_VER=%%v
    echo   PASS: VOICEVOX !VV_VER!
    set /a PASS_COUNT+=1
)

echo.
echo [4/8] VOICEVOX 指定話者の確認 (青山龍星 / ID:13)...
python -c ^
"import requests, json; ^
r=requests.get('http://127.0.0.1:50021/speakers',timeout=5); ^
spks=r.json(); ^
found=[s for s in spks if any(st['id']==13 for st in s.get('styles',[]))]; ^
print('FOUND' if found else 'NOT_FOUND')" > "%TEMP%\vv_speaker.txt" 2>nul
set /p VV_SPK=<"%TEMP%\vv_speaker.txt"
if "!VV_SPK!"=="FOUND" (
    echo   PASS: 青山龍星 (speaker ID: 13) が利用可能です
    set /a PASS_COUNT+=1
) else (
    echo   FAIL: 青山龍星 (ID: 13) が見つかりません
    echo   修正方法: VOICEVOX で青山龍星ライブラリをダウンロードしてください
    set /a FAIL_COUNT+=1
)

echo.
echo [5/8] 日本語フォントの確認 (Noto Sans CJK)...
if exist "C:\Windows\Fonts\NotoSansCJK-Bold.ttc" (
    echo   PASS: NotoSansCJK-Bold.ttc が見つかりました
    set /a PASS_COUNT+=1
) else (
    python -c ^
"from pathlib import Path; ^
dirs=['C:/Windows/Fonts', str(Path.home())+'/AppData/Local/Microsoft/Windows/Fonts']; ^
found=[str(p) for d in dirs for p in Path(d).glob('Noto*CJK*.ttc') if p.exists()]; ^
print(found[0] if found else '')" > "%TEMP%\font_check.txt" 2>nul
    set /p FONT_PATH=<"%TEMP%\font_check.txt"
    if "!FONT_PATH!"=="" (
        echo   WARN: NotoSansCJK フォントが見つかりません
        echo   修正方法:
        echo     https://github.com/googlefonts/noto-cjk/releases から
        echo     NotoSansCJK-Bold.ttc をダウンロードして C:\Windows\Fonts\ に配置
        echo     または: pip install fonttools  後にプロジェクトの fonts/ フォルダに配置
        set /a WARN_COUNT+=1
        echo   代替: Windows標準フォント (メイリオ等) を使用できます
    ) else (
        echo   PASS: !FONT_PATH!
        set /a PASS_COUNT+=1
    )
)

echo.
echo [6/8] BGM ファイルの確認 (昭和平成チャンネル用)...
set BGM_DIR=assets\bgm\showa_heisei
if not exist "%BGM_DIR%" (
    echo   FAIL: BGM ディレクトリが存在しません: %BGM_DIR%
    echo   修正方法: mkdir %BGM_DIR%  を実行してBGMファイルを配置してください
    set /a FAIL_COUNT+=1
) else (
    set BGM_FOUND=0
    for %%f in ("%BGM_DIR%\*.wav") do set BGM_FOUND=1 & set BGM_FILE=%%f
    if !BGM_FOUND!==1 (
        echo   PASS: !BGM_FILE!
        set /a PASS_COUNT+=1
        echo.
        echo   [BGM 権利確認]
        python -c ^
"import json; ^
r=json.load(open('assets/bgm/bgm_registry.json','r',encoding='utf-8')); ^
files=r.get('bgm_files',[]); ^
sh=[f for f in files if 'showa_heisei' in f.get('allowed_channels',[])]; ^
print('REGISTERED_FOR_SHOWA' if sh else 'NOT_REGISTERED')" > "%TEMP%\bgm_rights.txt" 2>nul
        set /p BGM_RIGHTS=<"%TEMP%\bgm_rights.txt"
        if "!BGM_RIGHTS!"=="REGISTERED_FOR_SHOWA" (
            echo   PASS: BGM は昭和平成チャンネルへの使用が許可されています
        ) else (
            echo   WARN: BGM ファイルが bgm_registry.json に未登録 または 昭和平成チャンネル未許可
            echo   修正方法: assets\bgm\bgm_registry.json を確認し、権利情報を登録してください
            set /a WARN_COUNT+=1
        )
    ) else (
        echo   FAIL: %BGM_DIR%\ に .wav ファイルが見つかりません
        echo   修正方法: 権利確認済みのBGMファイルを %BGM_DIR%\ に配置してください
        set /a FAIL_COUNT+=1
    )
)

echo.
echo [7/8] 書き込み権限の確認...
echo test > "%~dp0videos\.write_test" 2>nul
if %errorlevel% NEQ 0 (
    :: videosフォルダが無くてもOK（自動作成される）
    echo test > "%TEMP%\write_test_tmp.txt" 2>nul
    if !errorlevel! EQU 0 (
        del "%TEMP%\write_test_tmp.txt" > nul 2>&1
        echo   PASS: 書き込み権限あり (TEMP 経由で確認)
        set /a PASS_COUNT+=1
    ) else (
        echo   FAIL: 書き込み権限がありません
        echo   修正方法: このフォルダへの書き込み権限を確認してください
        set /a FAIL_COUNT+=1
    )
) else (
    del "%~dp0videos\.write_test" > nul 2>&1
    echo   PASS: 書き込み権限あり
    set /a PASS_COUNT+=1
)

echo.
echo [8/8] Python パッケージの確認...
python -c ^
"import sys; ^
pkgs={'pillow':'PIL','requests':'requests','numpy':'numpy','scipy':'scipy','anthropic':'anthropic','static_ffmpeg':'static_ffmpeg'}; ^
missing=[]; ^
[missing.append(k) for k,v in pkgs.items() if not __import__('importlib').util.find_spec(v)]; ^
print('MISSING:' + ','.join(missing) if missing else 'ALL_OK')" > "%TEMP%\pkg_check.txt" 2>nul
set /p PKG_STATUS=<"%TEMP%\pkg_check.txt"

if "!PKG_STATUS!"=="ALL_OK" (
    echo   PASS: 必要パッケージ全て確認済み
    set /a PASS_COUNT+=1
) else (
    set MISSING_PKGS=!PKG_STATUS:MISSING:=!
    echo   FAIL: 不足パッケージ: !MISSING_PKGS!
    echo   修正方法: pip install !MISSING_PKGS!
    set /a FAIL_COUNT+=1
)

:: ------------------------------------------------------------------
:: 総合結果
:: ------------------------------------------------------------------
echo.
echo ============================================================
echo   診断結果
echo ============================================================
echo   PASS: !PASS_COUNT! 項目
echo   WARN: !WARN_COUNT! 項目
echo   FAIL: !FAIL_COUNT! 項目
echo.

if !FAIL_COUNT! GTR 0 (
    echo   ❌ 本番実行できません。上記 FAIL 項目を修正してください。
) else if !WARN_COUNT! GTR 0 (
    echo   ⚠️  警告があります。WARN 項目を確認してください。
    echo   技術検証 (--test-mode) は実行可能です。
) else (
    echo   ✅ 全チェック PASS。本番実行できます。
    echo.
    echo   実行コマンド:
    echo     python create_video.py --channel showa_heisei --theme "テーマ名" --voicevox-speed 0.92
)
echo ============================================================

pause
endlocal
