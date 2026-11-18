"""一括実行オーケストレーター。

ステージ: research → script → assets → tts(実測で尺調整) → subtitles → bgm → render → qa
各ステージは独立して再実行可能(--job で既存ジョブを指定し --from / --only)。
"""
from __future__ import annotations

import argparse
import shutil
import sys
import traceback
from pathlib import Path

from .common import ROOT, Job, get_logger, load_json, new_job_id, save_json, settings

STAGES = ["research", "script", "assets", "tts", "subtitles", "bgm", "render", "qa"]


def main(argv=None):
    ap = argparse.ArgumentParser(description="皇室ニュース Shorts 自動制作")
    ap.add_argument("--topic", help="テーマ(例: 佳子さまの最新ニュース)。未指定なら候補から自動選定")
    ap.add_argument("--duration", type=float, default=60, help="最大尺(秒)")
    ap.add_argument("--job", help="既存ジョブIDを再開")
    ap.add_argument("--from", dest="from_stage", choices=STAGES, help="このステージから再実行")
    ap.add_argument("--only", choices=STAGES, help="このステージだけ実行")
    ap.add_argument("--script", help="手動で用意した script.json を使う(research/script をスキップ)")
    ap.add_argument("--tts-engine", choices=["voicevox", "openjtalk"])
    ap.add_argument("--no-bgm", action="store_true")
    ap.add_argument("--days", type=int, help="ニュース検索の遡り日数")
    a = ap.parse_args(argv)

    job = Job(a.job or new_job_id(a.topic))
    log = get_logger(job)
    log.info(f"=== ジョブ {job.id} / topic={a.topic!r} / 最大{a.duration}秒 ===")
    cfg = settings()
    cfg["output"]["max_duration"] = min(cfg["output"]["max_duration"], a.duration)
    max_narr = min(a.duration, 60) - 1.2  # 余白

    if a.script:
        shutil.copy(a.script, job.script)
    run_stages = STAGES
    if a.only:
        run_stages = [a.only]
    elif a.from_stage:
        run_stages = STAGES[STAGES.index(a.from_stage):]
    elif a.script or (a.job and job.script.exists()):
        run_stages = STAGES[2:]

    from . import assets, bgm, qa, render, research, script_writer, subtitles, tts

    def stage(name, fn):
        if name not in run_stages:
            return None
        log.info(f"--- {name} ---")
        try:
            return fn()
        except Exception as e:
            job.mark(name, False, error=str(e)[:500])
            log.error(f"{name} 失敗: {e}\n{traceback.format_exc()}")
            raise

    try:
        stage("research", lambda: research.run_research(job, a.topic, a.days))
        stage("script", lambda: script_writer.generate(job, a.topic, force="script" in run_stages and not a.script))
        script = load_json(job.script)
        if script is None:
            log.error(f"台本がありません: {job.script}")
            return 2
        stage("assets", lambda: assets.collect(job, script))

        def do_tts():
            nonlocal script
            for attempt in range(4):
                tl = tts.synthesize(job, script, a.tts_engine)
                if tl["duration"] <= max_narr:
                    if tl["duration"] < 40:
                        log.warning(f"ナレーションが短め({tl['duration']:.1f}秒)。台本の追加を検討してください")
                    return tl
                log.warning(f"ナレーション {tl['duration']:.1f}秒 > 上限 {max_narr:.1f}秒 → 台本を短縮 (試行{attempt + 1})")
                script = script_writer.shorten(job, script, tl["duration"] - max_narr, tl["duration"], log)
                save_json(job.script, script)
            raise RuntimeError("尺の調整に失敗しました")

        stage("tts", do_tts)
        script = load_json(job.script)
        timeline = load_json(job.timeline)
        stage("subtitles", lambda: subtitles.build(job, script, timeline))
        bgm_path = stage("bgm", lambda: bgm.prepare(job, timeline["duration"], False if a.no_bgm else None))
        if bgm_path is None and "bgm" not in run_stages:
            p = job.audio / "bgm.wav"
            bgm_path = p if p.exists() and not a.no_bgm else None
        stage("render", lambda: render.render(job, script, timeline, load_json(job.asset_manifest), bgm_path))
        res = stage("qa", lambda: qa.check(job))
        # 公開用メタデータ
        man = load_json(job.asset_manifest, {})
        meta = [f"タイトル: {script.get('youtube_title', '')}", "", script.get("description", ""), "",
                " ".join(script.get("hashtags", [])), "", "【出典】"]
        urls = {}
        for f in script.get("facts", []):
            if f.get("status") != "unverified" and f.get("url") and f["url"] not in script.get("description", ""):
                urls.setdefault(f["url"], f["source_name"])
        meta += [f"{n}: {u}" for u, n in urls.items()] or ["(概要欄本文に記載)"]
        shots = load_json(job.output / "shots.json", [])
        used = {str(Path(s["file"]).relative_to(ROOT)) for s in shots if s.get("file")}
        credits = sorted({f"{r['source_title'].split(':', 1)[-1]} / {r['rights_holder'] or '作者不明'} / {r['license']} / {r.get('source_url', '')}"
                          for k, r in man.get("files", {}).items() if k in used})
        meta += ["", "【写真クレジット】"] + credits
        meta += ["", ("BGM: オリジナル(自動生成)" if bgm_path and bgm_path.parent == job.audio else f"BGM: {bgm_path.name}" if bgm_path else "BGM: なし")]
        (job.output / "upload_metadata.txt").write_text("\n".join(meta), encoding="utf-8")
        log.info(f"=== 完了: {job.video} ===")
        if res is not None and not res["passed"]:
            log.warning("品質検査で要確認項目があります: " + str(job.qa))
        return 0
    except Exception:
        log.error(f"ジョブ {job.id} は途中で停止しました。修正後: ./run.sh --job {job.id} --from <stage>")
        return 1


if __name__ == "__main__":
    sys.exit(main())
