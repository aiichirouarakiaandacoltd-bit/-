#!/usr/bin/env bash
# VOICEVOX ENGINE(CPU版)を起動する。起動後は run.sh が自動で 青山龍星 を使う。
# 方法1: Docker が使える環境
#   docker run -d --name voicevox -p 50021:50021 voicevox/voicevox_engine:cpu-latest
# 方法2: Linux版エンジンを GitHub Releases から取得して起動(github.com 等へのアクセスが必要)
# ※ このスクリプトは構築時の環境で GitHub がブロックされていたため未検証
set -euo pipefail
DIR="${VOICEVOX_DIR:-$HOME/voicevox_engine}"
if curl -s -m 3 http://127.0.0.1:50021/version >/dev/null; then echo "VOICEVOX 起動済み"; exit 0; fi
if command -v docker >/dev/null && docker info >/dev/null 2>&1; then
  docker run -d --name voicevox -p 50021:50021 voicevox/voicevox_engine:cpu-latest
else
  if [[ ! -x "$DIR/run" ]]; then
    command -v 7z >/dev/null || (apt-get update -qq && apt-get install -y -qq p7zip-full)
    mkdir -p "$DIR" && cd "$DIR"
    urls=$(curl -s https://api.github.com/repos/VOICEVOX/voicevox_engine/releases/latest \
      | python3 -c "import sys,json;[print(a['browser_download_url']) for a in json.load(sys.stdin)['assets'] if 'linux-cpu-x64' in a['name'] and '.7z' in a['name']]")
    for u in $urls; do curl -L -O "$u"; done
    7z x -y ./*.7z.001 >/dev/null
    mv */* . 2>/dev/null || true
  fi
  cd "$DIR" && nohup ./run --host 127.0.0.1 --port 50021 > voicevox.log 2>&1 &
fi
until curl -s -m 2 http://127.0.0.1:50021/version >/dev/null; do sleep 2; done
echo "VOICEVOX 起動: $(curl -s http://127.0.0.1:50021/version)"
