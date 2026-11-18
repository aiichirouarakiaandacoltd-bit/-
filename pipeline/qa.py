"""ステージ8: 品質検査。

機械的に確認できる項目を検査し qa_report.json と確認用コンタクトシートを出力する。
人の目で確認すべき項目(事実・素材の人物同定・読み)は human_review に列挙する。
"""
from __future__ import annotations

import re

from .common import ROOT, Job, ffprobe, get_logger, load_json, run, save_json, settings


def check(job: Job) -> dict:
    log = get_logger(job)
    cfg = settings()["output"]
    v = job.video
    res = {"video": str(v.relative_to(ROOT)), "checks": [], "human_review": []}

    def add(name, ok, detail):
        res["checks"].append({"name": name, "ok": bool(ok), "detail": detail})

    info = ffprobe(v)
    vs = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    num, den = map(int, vs["r_frame_rate"].split("/"))
    add("解像度 1080x1920", (vs["width"], vs["height"]) == (cfg["width"], cfg["height"]), f"{vs['width']}x{vs['height']}")
    add("30fps", abs(num / den - cfg["fps"]) < 0.01, f"{num / den:.3f}")
    add("H.264", vs["codec_name"] == "h264", vs["codec_name"])
    add("AAC", au is not None and au["codec_name"] == "aac", au["codec_name"] if au else "音声なし")
    add(f"尺 {cfg['max_duration']}秒以内", dur <= cfg["max_duration"] + 0.05, f"{dur:.2f}秒")
    add("尺が短すぎない(45秒以上)", dur >= 45, f"{dur:.2f}秒")

    # 黒フレーム(映像の欠落)
    r = run(["ffmpeg", "-i", str(v), "-vf", "blackdetect=d=0.2:pix_th=0.08", "-an", "-f", "null", "-"], check=False)
    blacks = re.findall(r"black_start:([0-9.]+) black_end:([0-9.]+)", r.stderr)
    add("黒画面なし(映像の欠落)", not blacks, blacks or "なし")
    # 無音(ナレーションの欠落): 1.2秒以上の無音
    r = run(["ffmpeg", "-i", str(v), "-af", "silencedetect=n=-45dB:d=1.2", "-vn", "-f", "null", "-"], check=False)
    sil = re.findall(r"silence_start: ([0-9.]+)", r.stderr)
    sil = [float(s) for s in sil if float(s) < dur - 1.0]
    add("長い無音なし(ナレーション欠落)", not sil, sil or "なし")
    # ラウドネス
    r = run(["ffmpeg", "-i", str(v), "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"], check=False)
    I = re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)
    peak = re.findall(r"Peak:\s+(-?[0-9.]+) dBFS", r.stderr)
    I = float(I[-1]) if I else None
    add("ラウドネス -18〜-14 LUFS", I is not None and -18 <= I <= -14, f"{I} LUFS / peak {peak[-1] if peak else '?'} dBFS")

    # 音声・字幕の同期と速度
    tl = load_json(job.timeline)
    chunks = load_json(job.subs / "chunks.json", [])
    add("ナレーション速度 1.0", tl.get("speed") == 1.0, f"{tl.get('speed')} / {tl.get('engine_label')}")
    chars = sum(len(s["text"]) for sc in tl["scenes"] for s in sc["sentences"])
    add("ナレーション密度(参考≈6.5字/秒, 4.5〜7.5)", 4.5 <= chars / tl["duration"] <= 7.5, f"{chars / tl['duration']:.2f}字/秒")
    gaps = [round(b["start"] - a["end"], 2) for a, b in zip(chunks, chunks[1:]) if b["start"] - a["end"] > 0.05]
    add("字幕の途切れなし", not gaps, gaps or "なし")
    over = [c["lines"] for c in chunks if len(c["lines"]) > 2 or any(len(re.sub('[、。]', '', l)) > 13 for l in c["lines"])]
    add("字幕 2行以内・1行13字以内", not over, over or "OK")
    cover = (chunks[-1]["end"] - chunks[0]["start"]) / tl["duration"] if chunks else 0
    add("字幕がナレーション全体を覆う", cover > 0.9, f"{cover:.0%}")
    avg = sum(c["end"] - c["start"] for c in chunks) / max(1, len(chunks))
    add("字幕テンポ(参考≈1.2秒, 0.8〜2.2秒)", 0.8 <= avg <= 2.2, f"平均 {avg:.2f}秒 / {len(chunks)}チャンク")

    # 素材と台本
    shots = load_json(job.output / "shots.json", [])
    sd = [s["end"] - s["start"] for s in shots]
    add("カット割り(参考 平均3.5秒, 2.5〜5秒)", shots and 2.5 <= sum(sd) / len(sd) <= 5.0,
        f"{len(shots)}カット / 平均 {sum(sd) / max(1, len(sd)):.2f}秒 / 最短 {min(sd):.2f} 最長 {max(sd):.2f}")
    man = load_json(job.asset_manifest, {})
    bad = [f for f, r in man.get("files", {}).items() if not r["usage_decision"].startswith("利用可")]
    add("全素材の利用可否判定済み", not bad, bad or f"{len(man.get('files', {}))}ファイルすべて利用可")
    cards = sum(1 for s in shots if s["type"] == "card")
    add("図解カード比率 50%以下", cards <= len(shots) * 0.5, f"{cards}/{len(shots)}")
    script = load_json(job.script)
    from .script_writer import validate
    errs = validate(script)
    add("台本の出典・発言検証", not errs, errs or "OK")

    res["human_review"] = list(script.get("human_check", [])) + [
        "自動取得した写真に写っている人物が、台本の人物と一致しているか(Commonsのファイル名・説明に依存)",
        "固有名詞の読み(特に人名・地名・行事名)を音声で確認",
        "概要欄に素材クレジット(credits.txt)と出典URLを記載",
    ]
    if man.get("candidates_need_permission"):
        res["human_review"].append("宮内庁の写真を使う場合は事前に宮内庁広報室へ相談(candidates_need_permission 参照)")

    # コンタクトシート
    sheet = job.output / "contact_sheet.jpg"
    run(["ffmpeg", "-y", "-v", "error", "-i", str(v), "-vf", "fps=1/3,scale=216:384,tile=10x2", "-frames:v", "1", str(sheet)], check=False)
    res["contact_sheet"] = str(sheet.relative_to(ROOT))
    res["passed"] = all(c["ok"] for c in res["checks"])
    save_json(job.qa, res)
    for c in res["checks"]:
        log.info(f"  [{'OK' if c['ok'] else 'NG'}] {c['name']}: {c['detail'] if not isinstance(c['detail'], list) else str(c['detail'])[:120]}")
    log.info(f"品質検査: {'合格' if res['passed'] else '要確認あり'} → {job.qa}")
    job.mark("qa", res["passed"])
    return res
