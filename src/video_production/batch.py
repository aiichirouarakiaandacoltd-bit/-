"""バッチ処理モジュール

複数の台本JSONから一括で動画を生成する。

使い方:
  python -m src.video_production.batch --scripts-dir outputs/videos/scripts/
  python -m src.video_production.batch --script script1.json script2.json
"""

import argparse
import json
import sys
from pathlib import Path

from .pipeline import run_pipeline
from .script_generator import load_script


def batch_from_scripts(script_paths: list[Path]) -> list[dict]:
    results = []
    total = len(script_paths)

    for i, sp in enumerate(script_paths, 1):
        print(f"\n{'#'*60}")
        print(f"バッチ処理 [{i}/{total}]: {sp.name}")
        print(f"{'#'*60}")

        try:
            script = load_script(sp)
            result = run_pipeline(
                topic=script.get("title", ""),
                main_text="",
                video_format=script.get("format", "long"),
                title=script.get("title", ""),
                persons=script.get("persons"),
                source_urls=script.get("source_urls"),
                script_path=sp,
            )
            results.append(result)
        except Exception as e:
            print(f"[ERROR] {sp.name}: {e}")
            results.append({"status": "error", "reason": str(e), "script": str(sp)})

    print(f"\n{'='*60}")
    print("バッチ処理結果:")
    ok = sum(1 for r in results if r.get("status") == "completed")
    ng = total - ok
    print(f"  成功: {ok} / 失敗: {ng} / 合計: {total}")
    print(f"{'='*60}")

    return results


def main():
    parser = argparse.ArgumentParser(description="バッチ動画生成")
    parser.add_argument("--scripts-dir", help="台本ディレクトリ")
    parser.add_argument("--script", nargs="*", help="台本ファイル")
    args = parser.parse_args()

    paths = []
    if args.scripts_dir:
        d = Path(args.scripts_dir)
        paths.extend(sorted(d.glob("*.json")))
    if args.script:
        paths.extend(Path(s) for s in args.script)

    if not paths:
        print("[ERROR] 台本ファイルを指定してください。")
        sys.exit(1)

    batch_from_scripts(paths)


if __name__ == "__main__":
    main()
