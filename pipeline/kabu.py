"""bin/kabu — 係(サブエージェント)の進行を state.json で管理する道具。

工程(ステップ)は組織図の係に対応する。人の承認(荒木さん)は4か所:
  テーマ / 確認① / 確認② / 公開
メイン(/kabu の指揮)は `bin/kabu next` で次に動かす係を知り、係に仕事を渡し、
係の成果を `bin/kabu done <工程>` で記録して進める。

使い方:
  bin/kabu new --topic "雅子さま 久子さま 洋装"     新しい案件(ジョブ)を作る
  bin/kabu status [--job ID]                        進行状況
  bin/kabu next   [--job ID]                        次の工程と担当係・入出力
  bin/kabu done <工程> [--note ...]                 工程完了を記録
  bin/kabu fail <工程> --note "直し指示"            採点で不合格 → 差し戻し先に戻す
  bin/kabu approve <テーマ|確認1|確認2|公開>         荒木さんの承認
  bin/kabu run <工程>                               機械的な工程(調査・音声・字幕・書き出し等)を実行
  bin/kabu measure                                  書き出し結果の計測(尺・音量・一致度など)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from .common import ROOT, Job, load_json, new_job_id, now_jst, save_json

STATE_DIR = ROOT / "state"
CURRENT = STATE_DIR / "current"

# 工程の定義: (工程ID, 担当係, 種類, 説明, 差し戻し先)
# 種類: agent=係(サブエージェント)が判断する / tool=機械処理 / gate=荒木さんの承認 / check=採点の係
STEPS = [
    ("research", "棚調べ係", "tool", "ニュース候補の収集(宮内庁+報道)", None),
    ("brief", "企画係", "agent", "題材を選び brief.md を書く", None),
    ("gate_theme", "荒木さん", "gate", "テーマ承認", "brief"),
    ("script", "台本係", "agent", "台本と出典(script.json)", "brief"),
    ("factcheck", "事実確認係", "check", "公式出典と照合", "script"),
    ("rules_script", "決まりの確認係", "check", "台本の決まり(煽り禁止・発言の一字一句・尺)", "script"),
    ("gate_check1", "荒木さん", "gate", "確認①(台本・出典)", "script"),
    ("assets", "制作係", "tool", "素材の検索・権利確認・取得", None),
    ("layout", "画面割り係", "agent", "章ごとの画面割り(素材の割り当て・構図)", "assets"),
    ("tts", "書き出し係", "tool", "ナレーション(VOICEVOX:青山龍星)", None),
    ("subtitles", "書き出し係", "tool", "字幕", None),
    ("render", "書き出し係", "tool", "動画の書き出し(render)と計測(measure)", None),
    ("frames", "当てっこ係", "check", "コマごとの点検(崩れ・字幕・顔の隠れ)", "layout"),
    ("review", "確認係", "check", "採点と直し指示", "layout"),
    ("video_review", "動画の確認係", "check", "確認②の材料を作る", None),
    ("gate_check2", "荒木さん", "gate", "確認②(完成動画)", "layout"),
    ("shorts", "ショート係", "agent", "shorts.yaml(縦型の仕様・冒頭フック)", None),
    ("thumb_frames", "サムネ・タイトル係", "tool", "完成動画から候補フレーム5枚を抽出(タイムコード付き)", None),
    ("thumb_title", "サムネ・タイトル係", "agent", "サムネ文言3案(thumb.yaml)とタイトル3案・タグ・章・概要欄(publish.yaml)", None),
    ("thumb_render", "デザイナー(重要)", "tool", "サムネPNG 3案とCanvaの編集可能デザイン", "thumb_title"),
    ("rules_publish", "決まりの確認係", "check", "画面/投稿の決まり(権利・表記・文字)", "thumb_title"),
    ("gate_publish", "荒木さん", "gate", "公開承認", "thumb_title"),
]
STEP_IDS = [s[0] for s in STEPS]
GATES = {"テーマ": "gate_theme", "確認1": "gate_check1", "確認①": "gate_check1",
         "確認2": "gate_check2", "確認②": "gate_check2", "公開": "gate_publish"}


def _state_path(job_id: str) -> Path:
    return STATE_DIR / job_id / "state.json"


def current_job(job: str | None) -> str:
    if job:
        return job
    if CURRENT.exists():
        return CURRENT.read_text().strip()
    sys.exit("案件がありません: bin/kabu new --topic ... で作成してください")


def load(job_id: str) -> dict:
    st = load_json(_state_path(job_id))
    if not st:
        sys.exit(f"state.json がありません: {job_id}")
    return st


def save(st: dict):
    st["updated_at"] = now_jst().isoformat(timespec="seconds")
    save_json(_state_path(st["job_id"]), st)


def log_event(st, msg):
    st.setdefault("history", []).append({"at": now_jst().isoformat(timespec="seconds"), "event": msg})


def cmd_new(a):
    job_id = a.job or new_job_id(a.topic)
    Job(job_id)
    st = {"job_id": job_id, "topic": a.topic, "subject": a.subject, "duration": a.duration, "created_at": now_jst().isoformat(timespec="seconds"),
          "approver": "荒木さん", "auto_approve": a.auto_approve,
          "steps": {sid: {"status": "pending", "owner": owner, "kind": kind, "desc": desc}
                    for sid, owner, kind, desc, _ in STEPS}}
    log_event(st, f"案件作成 topic={a.topic}")
    save(st)
    STATE_DIR.mkdir(exist_ok=True)
    CURRENT.write_text(job_id)
    print(job_id)


def next_step(st):
    for sid in STEP_IDS:
        if st["steps"][sid]["status"] != "done":
            return sid
    return None


def paths(job_id):
    j = Job(job_id)
    return {"brief": str(j.scripts / "brief.md"), "script": str(j.script), "candidates": str(j.candidates),
            "assets": str(j.asset_manifest), "layout": str(j.scripts / "layout.json"), "timeline": str(j.timeline),
            "video": str(j.video), "qa": str(j.qa), "frames_dir": str(j.output / "frames"),
            "review": str(j.output / "review.md"), "shorts": str(j.scripts / "shorts.yaml"),
            "thumb": str(j.output / "thumb.yaml"), "publish": str(j.output / "publish.yaml"),
            "thumb_png_dir": str(j.output / "thumbs")}


def cmd_status(a):
    st = load(current_job(a.job))
    print(f"案件 {st['job_id']} / topic={st['topic']}")
    for sid, owner, kind, desc, _ in STEPS:
        s = st["steps"][sid]
        mark = {"done": "✔", "pending": "・", "failed": "✗", "waiting": "…"}.get(s["status"], "?")
        note = f"  ({s.get('note')})" if s.get("note") else ""
        print(f" {mark} {sid:14s} {owner:10s} {desc}{note}")


def cmd_next(a):
    st = load(current_job(a.job))
    sid = next_step(st)
    if not sid:
        print(json.dumps({"step": None, "message": "全工程完了"}, ensure_ascii=False))
        return
    owner, kind, desc, back = next((o, k, d, b) for s, o, k, d, b in STEPS if s == sid)
    out = {"job": st["job_id"], "step": sid, "owner": owner, "kind": kind, "desc": desc,
           "topic": st["topic"], "paths": paths(st["job_id"]), "send_back_to": back,
           "last_note": st["steps"][sid].get("note")}
    if kind == "gate" and st.get("auto_approve"):
        out["hint"] = "auto_approve=true: メインが承認を代行してよい(記録は残る)"
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_done(a):
    st = load(current_job(a.job))
    st["steps"][a.step].update(status="done", note=a.note or "", at=now_jst().isoformat(timespec="seconds"))
    log_event(st, f"完了 {a.step} {a.note or ''}")
    save(st)
    print(f"done {a.step}")


def cmd_fail(a):
    st = load(current_job(a.job))
    back = next(b for s, o, k, d, b in STEPS if s == a.step)
    st["steps"][a.step].update(status="failed", note=a.note)
    if back:
        i0 = STEP_IDS.index(back)
        for sid in STEP_IDS[i0:]:
            if st["steps"][sid]["status"] == "done":
                st["steps"][sid]["status"] = "pending"
        st["steps"][back]["note"] = f"差し戻し({a.step}): {a.note}"
    st.setdefault("retries", {}).setdefault(a.step, 0)
    st["retries"][a.step] += 1
    log_event(st, f"不合格 {a.step} → {back}: {a.note}")
    save(st)
    print(f"fail {a.step} → back to {back} (retry {st['retries'][a.step]})")


def cmd_approve(a):
    st = load(current_job(a.job))
    sid = GATES.get(a.gate, a.gate)
    st["steps"][sid].update(status="done", note=f"承認: {st.get('approver')}" + (f" / {a.note}" if a.note else ""),
                            at=now_jst().isoformat(timespec="seconds"))
    log_event(st, f"承認 {sid}")
    save(st)
    print(f"approved {sid}")


def _py(*args):
    r = subprocess.run([sys.executable, "-m", *args], cwd=ROOT)
    if r.returncode:
        sys.exit(r.returncode)


def cmd_run(a):
    st = load(current_job(a.job))
    j = st["job_id"]
    step = a.step
    dur = str(st.get("duration", 60))
    if step == "research":
        _py("pipeline.research", "--job", j, "--topic", st["topic"], "--days", str(a.days or 60))
    elif step == "assets":
        _py("pipeline.main", "--job", j, "--only", "assets", "--duration", dur)
    elif step in ("tts", "subtitles", "bgm", "qa"):
        _py("pipeline.main", "--job", j, "--only", step, "--duration", dur)
    elif step == "render":  # BGM → 書き出し → 品質検査
        _py("pipeline.main", "--job", j, "--from", "bgm", "--duration", dur, "--match-reference")
    elif step == "frames":
        _py("pipeline.frame_check", "--job", j)
    elif step == "thumb_frames":
        _py("pipeline.thumbnail", "--job", j, "--extract")
    elif step == "thumb_render":
        _py("pipeline.thumbnail", "--job", j, "--render")
    elif step == "script":  # 台本係の下書き(事実確認つき)を claude -p で作る
        args = ["pipeline.script_writer", "--job", j, "--topic", st["topic"], "--force"]
        brief = Job(j).scripts / "brief.md"
        if brief.exists():
            args += ["--brief", str(brief)]
        _py(*args)
    else:
        sys.exit(f"{step} は機械処理ではありません(係が判断する工程)")


def cmd_measure(a):
    j = Job(current_job(a.job))
    _py("pipeline.main", "--job", j.id, "--only", "qa")
    q = load_json(j.qa)
    print(json.dumps({"passed": q["passed"], "ng": [c for c in q["checks"] if not c["ok"]]}, ensure_ascii=False, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="kabu")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("new"); p.add_argument("--topic", required=True); p.add_argument("--job")
    p.add_argument("--duration", type=float, default=60); p.add_argument("--auto-approve", action="store_true")
    p.add_argument("--subject", help="主役人物(サムネイル用。例: 雅子さま,久子さま)")
    for n in ("status", "next", "measure"):
        p = sp.add_parser(n); p.add_argument("--job")
    p = sp.add_parser("done"); p.add_argument("step", choices=STEP_IDS); p.add_argument("--note"); p.add_argument("--job")
    p = sp.add_parser("fail"); p.add_argument("step", choices=STEP_IDS); p.add_argument("--note", required=True); p.add_argument("--job")
    p = sp.add_parser("approve"); p.add_argument("gate"); p.add_argument("--note"); p.add_argument("--job")
    p = sp.add_parser("run"); p.add_argument("step"); p.add_argument("--job"); p.add_argument("--days", type=int)
    a = ap.parse_args(argv)
    {"new": cmd_new, "status": cmd_status, "next": cmd_next, "done": cmd_done, "fail": cmd_fail,
     "approve": cmd_approve, "run": cmd_run, "measure": cmd_measure}[a.cmd](a)


if __name__ == "__main__":
    main()
