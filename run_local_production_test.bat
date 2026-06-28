@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ============================================================
echo   ザ・ダンク ローカル本番テスト実行
echo   run_local_production_test.bat
echo ============================================================
echo.

REM --- Step 1: Python確認 ---
echo [Step 1/19] Python確認...
python --version >nul 2>&1
if errorlevel 1 (
    echo   FAIL: Pythonが見つかりません。
    echo   停止箇所: Step 1 - Python確認
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo   OK: %%v

REM --- Step 2: FFmpeg確認 ---
echo [Step 2/19] FFmpeg確認...
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo   FAIL: FFmpegが見つかりません。
    echo   停止箇所: Step 2 - FFmpeg確認
    echo   対処: https://ffmpeg.org/ からダウンロードしてPATHに追加してください。
    pause
    exit /b 1
)
echo   OK

REM --- Step 3: ffprobe確認 ---
echo [Step 3/19] ffprobe確認...
ffprobe -version >nul 2>&1
if errorlevel 1 (
    echo   FAIL: ffprobeが見つかりません。FFmpegと一緒にインストールされます。
    echo   停止箇所: Step 3 - ffprobe確認
    pause
    exit /b 1
)
echo   OK

REM --- Step 4: yt-dlp確認 ---
echo [Step 4/19] yt-dlp確認...
yt-dlp --version >nul 2>&1
if errorlevel 1 (
    echo   FAIL: yt-dlpが見つかりません。
    echo   停止箇所: Step 4 - yt-dlp確認
    echo   対処: pip install yt-dlp を実行してください。
    pause
    exit /b 1
)
echo   OK

REM --- Step 5: VOICEVOX接続確認 ---
echo [Step 5/19] VOICEVOX接続確認...
curl -s -o nul -w "%%{http_code}" http://localhost:50021/version > "%TEMP%\vv_status.txt" 2>nul
set /p VV_STATUS=<"%TEMP%\vv_status.txt"
del "%TEMP%\vv_status.txt" 2>nul
if not "%VV_STATUS%"=="200" (
    echo   FAIL: VOICEVOXが応答しません。
    echo   停止箇所: Step 5 - VOICEVOX接続確認
    echo   対処: VOICEVOXを起動してから再実行してください。
    echo   ダウンロード: https://voicevox.hiroshiba.jp/
    pause
    exit /b 1
)
echo   OK

REM --- Step 6: 設定ファイル確認 ---
echo [Step 6/19] 設定ファイル確認...
set CONFIG_OK=1
if not exist "config\settings.json" (
    echo   FAIL: config\settings.json が見つかりません。
    set CONFIG_OK=0
)
if not exist "config\source_permissions.json" (
    echo   FAIL: config\source_permissions.json が見つかりません。
    set CONFIG_OK=0
)
if not exist "config\player_aliases.json" (
    echo   FAIL: config\player_aliases.json が見つかりません。
    set CONFIG_OK=0
)
if "%CONFIG_OK%"=="0" (
    echo   停止箇所: Step 6 - 設定ファイル確認
    pause
    exit /b 1
)
echo   OK

REM --- Step 7: 出力フォルダ準備 ---
echo [Step 7/19] 出力フォルダ準備...
if not exist "outputs\production" mkdir "outputs\production"
if not exist "output" mkdir "output"
echo   OK

REM --- Step 8: YouTube接続確認 ---
echo [Step 8/19] YouTube接続確認...
yt-dlp --simulate --flat-playlist --playlist-end 1 "https://www.youtube.com/@and-a9949/videos" >nul 2>&1
if errorlevel 1 (
    echo   WARNING: YouTubeへの接続に問題がある可能性があります。
    echo            ネットワーク接続を確認してください。
    echo            パイプラインは続行しますが、自動取得が失敗する可能性があります。
) else (
    echo   OK
)

REM --- Step 9: 本番パイプライン実行 ---
echo.
echo [Step 9/19] 本番パイプライン実行中...
echo ============================================================
echo.

python main.py --mode production
set PIPELINE_RESULT=%errorlevel%

echo.
echo ============================================================

if %PIPELINE_RESULT% neq 0 (
    echo.
    echo   FAIL: パイプラインがエラーで終了しました (exit code: %PIPELINE_RESULT%)
    echo   停止箇所: Step 9 - 本番パイプライン実行
    echo.
    echo   確認してください:
    echo     - outputs\production\ 内の最新フォルダの execution.log
    echo     - コンソール出力のエラーメッセージ
    echo.
    echo ============================================================
    pause
    exit /b 1
)

REM --- Step 10: 最新出力フォルダ検出 ---
echo [Step 10/19] 出力フォルダ検出...
set LATEST_DIR=
for /f "delims=" %%d in ('dir /b /ad /od "outputs\production" 2^>nul') do (
    set LATEST_DIR=%%d
)

if "%LATEST_DIR%"=="" (
    echo   FAIL: production出力フォルダが見つかりません。
    echo   停止箇所: Step 10 - 出力フォルダ検出
    pause
    exit /b 1
)

set OUT_PATH=outputs\production\%LATEST_DIR%
echo   OK: %OUT_PATH%

REM --- Step 11: final.mp4 存在確認 ---
echo [Step 11/19] final.mp4 存在確認...
if not exist "%OUT_PATH%\final.mp4" (
    echo   FAIL: final.mp4 が見つかりません。
    echo   停止箇所: Step 11 - final.mp4 存在確認
    echo   確認: %OUT_PATH%\execution.log
    pause
    exit /b 1
)
echo   OK: %OUT_PATH%\final.mp4

REM --- Step 12: 0KB確認 ---
echo [Step 12/19] 0KB確認...
for %%f in ("%OUT_PATH%\final.mp4") do set FSIZE=%%~zf
if "%FSIZE%"=="0" (
    echo   FAIL: final.mp4 が 0KB です。動画生成に失敗しています。
    echo   停止箇所: Step 12 - 0KB確認
    echo   確認: %OUT_PATH%\execution.log
    pause
    exit /b 1
)
echo   OK: %FSIZE% bytes

REM --- Step 13: ffprobe結果表示 ---
echo [Step 13/19] ffprobe検証...
echo.
echo   --- ffprobe結果 ---
ffprobe -v quiet -print_format json -show_format -show_streams "%OUT_PATH%\final.mp4" > "%TEMP%\ffprobe_result.json" 2>nul
if errorlevel 1 (
    echo   FAIL: ffprobeが失敗しました。ファイルが破損している可能性があります。
    echo   停止箇所: Step 13 - ffprobe検証
    pause
    exit /b 1
)
python -c "import json; d=json.load(open(r'%TEMP%\ffprobe_result.json','r')); vs=[s for s in d.get('streams',[]) if s.get('codec_type')=='video']; a=[s for s in d.get('streams',[]) if s.get('codec_type')=='audio']; v=vs[0] if vs else {}; au=a[0] if a else {}; fmt=d.get('format',{}); print(f'  解像度: {v.get(\"width\",\"?\")}x{v.get(\"height\",\"?\")}'); print(f'  映像コーデック: {v.get(\"codec_name\",\"?\")}'); print(f'  ピクセルフォーマット: {v.get(\"pix_fmt\",\"?\")}'); print(f'  FPS: {v.get(\"r_frame_rate\",\"?\")}'); print(f'  音声コーデック: {au.get(\"codec_name\",\"?\")}'); print(f'  再生時間: {float(fmt.get(\"duration\",0)):.2f}秒'); print(f'  ファイルサイズ: {int(fmt.get(\"size\",0))/1024/1024:.2f} MB')"
del "%TEMP%\ffprobe_result.json" 2>nul
echo.

REM --- Step 14: 自動取得情報表示 ---
echo [Step 14/19] 自動取得情報...
if exist "%OUT_PATH%\auto_fetch_report.json" (
    echo.
    echo   --- 自動取得情報 ---
    python -c "import json; d=json.load(open(r'%OUT_PATH%\auto_fetch_report.json','r',encoding='utf-8')); print(f'  元動画タイトル: {d.get(\"source_video\",\"不明\")}'); print(f'  URL: {d.get(\"source_url\",\"不明\")}'); r=d.get('rights',{}); print(f'  channel_source_permission: {r.get(\"channel_source_permission\",\"UNKNOWN\")}'); print(f'  embedded_footage_rights: {r.get(\"embedded_footage_rights\",\"UNKNOWN\")}'); print(f'  metadata_risk_status: {r.get(\"metadata_risk_status\",\"UNKNOWN\")}'); print(f'  audio_removed: {r.get(\"audio_removed\",False)}')"
    echo.
) else (
    echo   (自動取得なし - 手動指定またはビジュアル生成)
)

REM --- Step 15: publishable判定表示 ---
echo [Step 15/19] publishable判定...
if exist "%OUT_PATH%\publishable.json" (
    echo.
    echo   --- publishable判定 ---
    python -c "import json; d=json.load(open(r'%OUT_PATH%\publishable.json','r',encoding='utf-8')); print(f'  technical_publishable: {d.get(\"technical_publishable\",False)}'); print(f'  manual_review_required: {d.get(\"manual_review_required\",True)}'); print(f'  publishable: {d.get(\"publishable\",False)}'); bl=d.get('publish_blockers',[]); [print(f'    - {b}') for b in bl] if bl else print('  (投稿可能条件を全て満たしています)') if d.get('publishable') else None"
    echo.
) else (
    echo   FAIL: publishable.json が見つかりません。
    echo   停止箇所: Step 15 - publishable判定
)

REM --- Step 16: 品質レポート表示 ---
echo [Step 16/19] 品質レポート...
if exist "%OUT_PATH%\quality_report.json" (
    echo.
    echo   --- 品質検査結果 ---
    python -c "import json; d=json.load(open(r'%OUT_PATH%\quality_report.json','r',encoding='utf-8')); [print(f'  [{\"PASS\" if c[\"pass\"] else \"FAIL\"}] {c[\"name\"]}: {c[\"detail\"]}') for c in d.get('checks',[])]"
    echo.
) else (
    echo   WARNING: quality_report.json が見つかりません。
)

REM --- Step 17: metadata/report 場所表示 ---
echo [Step 17/19] metadata/report 場所...
echo.
echo   --- 生成物の場所 ---
echo   正式MP4:       %OUT_PATH%\final.mp4
if exist "output\final.mp4" (
    echo   互換コピー:     output\final.mp4 (正式保存先ではない)
)
echo   出力フォルダ:   %OUT_PATH%
if exist "%OUT_PATH%\status.json"          echo   status:         %OUT_PATH%\status.json
if exist "%OUT_PATH%\publishable.json"     echo   publishable:    %OUT_PATH%\publishable.json
if exist "%OUT_PATH%\quality_report.json"  echo   quality_report: %OUT_PATH%\quality_report.json
if exist "%OUT_PATH%\rights_report.md"     echo   rights_report:  %OUT_PATH%\rights_report.md
if exist "%OUT_PATH%\auto_fetch_report.json" echo   auto_fetch:     %OUT_PATH%\auto_fetch_report.json
if exist "%OUT_PATH%\execution.log"        echo   execution_log:  %OUT_PATH%\execution.log
if exist "%OUT_PATH%\summary.md"           echo   summary:        %OUT_PATH%\summary.md
echo.

REM --- Step 18: スクリーンショット表示 ---
echo [Step 18/19] スクリーンショット...
if exist "%OUT_PATH%\screenshots" (
    echo   スクリーンショット: %OUT_PATH%\screenshots
    dir /b "%OUT_PATH%\screenshots\*.png" 2>nul | find /c /v "" > "%TEMP%\ss_count.txt"
    set /p SS_COUNT=<"%TEMP%\ss_count.txt"
    del "%TEMP%\ss_count.txt" 2>nul
    echo   枚数: !SS_COUNT! 枚
) else (
    echo   (スクリーンショットなし)
)
for /d %%r in ("%OUT_PATH%\*review*") do (
    echo   確認用フレーム: %%r
)
echo.

REM --- Step 19: 最終サマリー ---
echo [Step 19/19] 最終サマリー
echo ============================================================
echo.
echo   正式出力:   %OUT_PATH%\final.mp4
echo   ファイルサイズ: %FSIZE% bytes
echo.

if exist "%OUT_PATH%\publishable.json" (
    python -c "import json; d=json.load(open(r'%OUT_PATH%\publishable.json','r',encoding='utf-8')); p=d.get('publishable',False); tp=d.get('technical_publishable',False); mr=d.get('manual_review_required',True); print(f'  publishable: {p}'); print(f'  technical_publishable: {tp}'); print(f'  manual_review_required: {mr}'); bl=d.get('publish_blockers',[]); print(); [print(f'  投稿不可理由: {b}') for b in bl] if bl else None"
)

echo.
echo ============================================================
if exist "%OUT_PATH%\publishable.json" (
    python -c "import json,sys; d=json.load(open(r'%OUT_PATH%\publishable.json','r',encoding='utf-8')); p=d.get('publishable',False); print('  publishable=true: 荒木による目視確認後に投稿可能です。') if p else print('  publishable=false: 上記の理由を確認してください。投稿しないでください。')"
) else (
    echo   publishable判定が取得できませんでした。投稿しないでください。
)
echo ============================================================
echo.

pause
