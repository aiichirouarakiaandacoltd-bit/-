#!/usr/bin/env bash
# 皇室ニュース Shorts 自動制作 — 1コマンド実行
#   ./run.sh --topic "佳子さまの最新ニュース" --duration 60
#   ./run.sh                       # テーマ未指定: ニュース候補から自動選定
#   ./run.sh --job <ID> --from tts # 途中から再実行
#   ./run.sh --analyze references/xxx.mp4  # 参考動画の分析
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${1:-}" == "--setup" ]]; then
  pip install -q -r requirements.txt
  command -v ffmpeg >/dev/null || { apt-get update -qq && apt-get install -y -qq ffmpeg; }
  fc-list | grep -q "Noto Sans CJK JP" || { apt-get update -qq && apt-get install -y -qq fonts-noto-cjk fonts-noto-cjk-extra; }
  echo "setup done"; exit 0
fi
if [[ "${1:-}" == "--analyze" ]]; then
  shift; exec python3 -m pipeline.analyze_reference "$@"
fi

python3 -c "import pyopenjtalk, cv2, PIL, numpy, requests" 2>/dev/null || {
  echo "依存パッケージ不足: ./run.sh --setup を実行してください" >&2; exit 1; }
exec python3 -m pipeline.main "$@"
