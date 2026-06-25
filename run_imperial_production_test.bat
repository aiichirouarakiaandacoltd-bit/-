@echo off
chcp 65001 >nul
echo ============================================================
echo  テスト実行 - 日本が誇る皇室物語 動画製作システム
echo  ※ テストモード（TEST ONLY）で実行します
echo  ※ 自動投稿は行いません
echo ============================================================
echo.

REM 環境チェック
echo [事前チェック] VOICEVOX確認中...
curl -s -o nul -w "%%{http_code}" http://127.0.0.1:50021/speakers 2>nul | findstr "200" >nul
if errorlevel 1 (
    echo   VOICEVOX未検出 → テストモードで続行（espeak-ng使用）
) else (
    echo   VOICEVOX: OK
)
echo.

set TOPIC=愛子さまの御名の由来
set TEXT_FILE=data\processed\test_draft.txt

if not exist "%TEXT_FILE%" (
    echo テスト用テキストを生成中...
    mkdir data\processed 2>nul
    echo 敬宮愛子内親王殿下の御名「愛子」は、孟子の「仁者は人を愛す」に由来するとされています。この御名には、人を思いやる心を持つ人であってほしいという願いが込められています。> "%TEXT_FILE%"
)

echo.
echo === Shortsテスト ===
python -m src.video_production ^
    --topic "%TOPIC%" ^
    --text-file "%TEXT_FILE%" ^
    --format shorts ^
    --test-mode

echo.
echo === 完了 ===
echo 出力先: outputs\videos_test\
echo.
echo ※ 最終判断・台本確定・投稿判断は荒木が行います。
echo ※ 自動投稿は行いません。
echo.
pause
