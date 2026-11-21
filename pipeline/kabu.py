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
# 制作ルール(docs/production_rules.md 2026-11-21版)の G0〜G5。荒木さんの承認は G0(企画)と G3(台本)の2か所。
STEPS = [
    ("env_check", "書き出し係", "tool", "第0-2章 作業前チェック(ツール・VOICEVOX・BGM・Noto Sans JP)→ env_check.md", None),
    ("research", "棚調べ係", "tool", "ニュース・題材候補の収集(宮内庁+報道)", None),
    ("plan", "企画係", "agent", "G0 企画: 題材・型(A比較/B人物物語/C一場面)・疑問・回答の要旨・100点評価 → plan.md", None),
    ("gate_G0", "荒木さん", "gate", "G0 企画の承認", "plan"),
    ("facts", "事実確認係", "check", "G1 事実: 宮内庁→官公庁→主催者→主要報道→史料で照合、公式事実/報道/分析を区別 → facts.md", "plan"),
    ("images", "制作係", "agent", "G2 素材: 人物画像をキャプションで特定して収集 → ledger.csv(目標の70%未満なら停止)", "plan"),
    ("script", "台本係", "agent", "G3 台本: 完成ナレーション script.md と場面設計 scenes.json(画像・切り抜き・動き・人物名・撮影情報)", "facts"),
    ("rules_script", "決まりの確認係", "check", "本書の禁止事項・第4章・第6章(省略禁止)で台本と場面設計を採点", "script"),
    ("gate_G3", "荒木さん", "gate", "G3 台本の承認", "script"),
    ("render", "書き出し係", "tool", "G4 生成: 音声(青山龍星0.90)・字幕(Noto Sans JP)・映像・BGM → output/<番号>_<縦型|横型>_internal.mp4", None),
    ("frames", "当てっこ係", "check", "コマごとの点検(人物の取り違え・崩れ・字幕・ラベル)", "script"),
    ("qa", "確認係", "tool", "G5 検査: 第8章の自動検査 → qa_report.md(全合格のみ完成)", "script"),
    ("pub_title", "タイトル係", "agent", "G6① タイトル: CTR20%以上を狙う99文字以内・ハッシュタグ付き → publish.yaml の title(本書第9章)", "script"),
    ("thumb_title", "タイトル係", "agent", "G6② 表紙: タイトルから3段見出しを流用し中心画像(台帳番号)を確定 → publish.yaml の thumb・thumb.yaml(赤は使わない)", "pub_title"),
    ("thumb_render", "デザイナー(重要)", "tool", "表紙画像PNGとCanvaの編集可能デザイン", "thumb_title"),
    ("pub_desc", "説明文係", "agent", "G6③ 説明文: タイトルから本文・参考資料を書き、templates/description_template.md でフルバージョンに組み立て → publish/description.txt", "pub_title"),
    ("pub_check", "確認係", "tool", "G6 検査: python -m pipeline.publish_text(99文字・3段の流用・末尾カンマ・5000文字)→ publish/check.md", "pub_desc"),
]
STEP_IDS = [s[0] for s in STEPS]
GATES = {"G0": "gate_G0", "企画": "gate_G0", "G3": "gate_G3", "台本": "gate_G3"}


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
    # 工程の追加・改称に追従(古い案件にも新しい工程を足し、工程順に並べ直す)
    old = st.get("steps", {})
    st["steps"] = {sid: {**{"status": "pending"}, **old.get(sid, {}), "owner": owner, "kind": kind, "desc": desc}
                   for sid, owner, kind, desc, _ in STEPS}
    return st


def save(st: dict):
    st["updated_at"] = now_jst().isoformat(timespec="seconds")
    save_json(_state_path(st["job_id"]), st)


def log_event(st, msg):
    st.setdefault("history", []).append({"at": now_jst().isoformat(timespec="seconds"), "event": msg})


def cmd_new(a):
    job_id = a.job or new_job_id(a.topic)
    Job(job_id)
    st = {"job_id": job_id, "topic": a.topic, "subject": a.subject, "kind": a.kind, "duration": a.duration, "created_at": now_jst().isoformat(timespec="seconds"),
          "approver": "荒木さん", "auto_approve": False, "rules": "docs/production_rules.md(2026-11-21)",
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
    p = ROOT / "projects" / job_id
    return {"project_dir": str(p), "env_check": str(p / "env_check.md"), "plan": str(p / "plan.md"),
            "facts": str(p / "facts.md"), "ledger": str(p / "ledger.csv"), "assets": str(ROOT / "assets" / job_id),
            "script": str(p / "script.md"), "scenes": str(p / "scenes.json"), "readings": str(p / "readings.json"),
            "video_dir": str(p / "output"), "qa": str(p / "qa_report.md"), "rules": str(ROOT / "docs" / "production_rules.md"),
            "candidates": str(ROOT / "research" / job_id / "candidates.json"), "thumb": str(p / "thumb.yaml")}


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
    kind = st.get("kind", "縦型")
    step = a.step
    if step == "env_check":
        _py("pipeline.env_check", "--project", j)
    elif step == "research":
        _py("pipeline.research", "--job", j, "--topic", st["topic"], "--days", str(a.days or 60))
    elif step == "images":  # 例: bin/kabu run images --pages URL... --commons "Princess Aiko"
        _py("pipeline.collect_images", "--project", j, "--pages", *(a.pages or []), "--commons", *(a.commons or []))
    elif step == "render":
        _py("pipeline.rules_render", "--project", j, "--kind", kind)
    elif step == "qa":
        _py("pipeline.qa_rules", "--project", j, "--kind", kind)
    elif step == "frames":
        _py("pipeline.frame_check", "--video", str(ROOT / "projects" / j / "output" / f"{j}_{kind}_internal.mp4"),
            "--out", str(ROOT / "projects" / j / "output" / "frames"))
    elif step == "pub_check":
        _py("pipeline.publish_text", "--project", j)
    elif step == "thumb_render":
        _py("pipeline.thumbnail", "--job", j, "--render")
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
    p.add_argument("--duration", type=float, default=60)
    p.add_argument("--subject", help="主役人物(例: 愛子内親王殿下)")
    p.add_argument("--kind", default="縦型", choices=["縦型", "横型"])
    for n in ("status", "next", "measure"):
        p = sp.add_parser(n); p.add_argument("--job")
    p = sp.add_parser("done"); p.add_argument("step", choices=STEP_IDS); p.add_argument("--note"); p.add_argument("--job")
    p = sp.add_parser("fail"); p.add_argument("step", choices=STEP_IDS); p.add_argument("--note", required=True); p.add_argument("--job")
    p = sp.add_parser("approve"); p.add_argument("gate"); p.add_argument("--note"); p.add_argument("--job")
    p = sp.add_parser("run"); p.add_argument("step"); p.add_argument("--job"); p.add_argument("--days", type=int)
    p.add_argument("--pages", nargs="*"); p.add_argument("--commons", nargs="*")
    a = ap.parse_args(argv)
    {"new": cmd_new, "status": cmd_status, "next": cmd_next, "done": cmd_done, "fail": cmd_fail,
     "approve": cmd_approve, "run": cmd_run, "measure": cmd_measure}[a.cmd](a)


if __name__ == "__main__":
    main()
