"""ステージ2: 事実確認 + 台本生成。

バックエンド(config/settings.json research.llm_backend_order の順に試行):
  - claude_cli   : Claude Code のヘッドレス実行 `claude -p`(WebSearch/WebFetch で記事本文を確認)
  - anthropic_api: ANTHROPIC_API_KEY がある場合、Messages API + web_search ツール(未検証)
どちらも使えない場合は prompt を scripts/<job>/prompt.md に書き出して停止する(手動で script.json を置けば続行可)。

出力: scripts/<job>/script.json
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess

import requests

from .common import ROOT, Job, get_logger, load_json, save_json, settings, style

MIN_CHARS, MAX_CHARS = 280, 340


class ScriptError(RuntimeError):
    pass


def _structure_text() -> str:
    tpl = style()["rules"]["script_template"]
    return "\n".join(f"   - {t['sec'][0]}〜{t['sec'][1]}秒 [{t['role']}]: {t['desc']}" for t in tpl)


def _candidates_text(job: Job, topic: str | None, n=10) -> str:
    data = load_json(job.candidates, {"candidates": []})
    lines = []
    for k, c in enumerate(data["candidates"][:n], 1):
        lines.append(f"候補{k}: {c['headline']} (信頼ソース{c['trusted_source_count']}件, 一次情報={'あり' if c['has_primary'] else 'なし'})")
        for i in c["items"][:6]:
            lines.append(f"  - [{i['tier']}] {i['source']} {i.get('published')} 「{i['title'][:70]}」 {i['url'][:160]}")
    return "\n".join(lines) or "(候補なし: 題材の指定に基づき自分で検索すること)"


def build_prompt(job: Job, topic: str | None, min_chars=MIN_CHARS, max_chars=MAX_CHARS) -> str:
    tpl = (ROOT / "templates" / "script_prompt.md").read_text(encoding="utf-8")
    topic_line = f"「{topic}」に合う題材を候補から選ぶ。候補に無ければ自分で検索して最新の確認可能なニュースを選ぶ。" if topic \
        else "指定なし。候補の中から最も動画化に適した題材を選ぶ。"
    return tpl.format(channel=settings()["channel_name"], topic_line=topic_line,
                      candidates=_candidates_text(job, topic), structure=_structure_text(),
                      min_chars=min_chars, max_chars=max_chars)


def extract_json(text: str) -> dict:
    blocks = re.findall(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    cand = blocks[-1] if blocks else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(cand)


def _claude_cli(prompt: str, log, timeout=1500) -> str:
    exe = shutil.which("claude")
    if not exe:
        raise ScriptError("claude CLI が見つかりません")
    cmd = [exe, "-p", "--output-format", "json", "--allowedTools", "WebSearch", "WebFetch", "--max-turns", "40"]
    model = settings()["research"].get("claude_cli_model")
    if model:
        cmd += ["--model", model]
    log.info("claude -p で事実確認・台本生成中(数分かかります)…")
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise ScriptError(f"claude CLI 失敗: {r.stderr[-800:]}")
    try:
        out = json.loads(r.stdout)
        return out.get("result", "")
    except json.JSONDecodeError:
        return r.stdout


def _anthropic_api(prompt: str, log) -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise ScriptError("ANTHROPIC_API_KEY 未設定")
    model = settings()["research"]["anthropic_model"]
    body = {
        "model": model, "max_tokens": 16000,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 15}],
        "messages": [{"role": "user", "content": prompt}],
    }
    r = requests.post(os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com") + "/v1/messages",
                      headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                      json=body, timeout=900)
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json()["content"] if b.get("type") == "text")


def call_llm(prompt: str, log) -> str:
    errs = []
    for be in settings()["research"]["llm_backend_order"]:
        try:
            return {"claude_cli": _claude_cli, "anthropic_api": _anthropic_api}[be](prompt, log)
        except Exception as e:
            errs.append(f"{be}: {e}")
            log.warning(f"LLMバックエンド {be} 使用不可: {e}")
    raise ScriptError("利用可能なLLMバックエンドがありません: " + " / ".join(errs))


def validate(script: dict) -> list[str]:
    """台本の機械的チェック。致命的な問題のリストを返す。"""
    errs = []
    facts = {f["id"]: f for f in script.get("facts", [])}
    if not script.get("scenes"):
        errs.append("scenes が空")
    for f in facts.values():
        if not f.get("url"):
            errs.append(f"{f['id']}: 出典URLなし")
    for s in script.get("scenes", []):
        if not s.get("narration"):
            errs.append(f"{s['id']}: narration が空")
        for fid in s.get("fact_ids", []):
            if fid not in facts:
                errs.append(f"{s['id']}: 未定義の fact_id {fid}")
            elif facts[fid].get("status") == "unverified":
                errs.append(f"{s['id']}: 未確認の事実 {fid} を使用")
        if s.get("role") not in ("hook", "closing") and not s.get("fact_ids"):
            errs.append(f"{s['id']}: 事実の根拠(fact_ids)なし")
        # かぎかっこの発言は facts の quote/claim に一字一句含まれていること
        for q in re.findall(r"「([^」]+)」", s.get("narration", "")):
            src = " ".join((facts[i].get("quote", "") + " " + facts[i].get("claim", "")) for i in s.get("fact_ids", []) if i in facts)
            if q not in src:
                errs.append(f"{s['id']}: 発言「{q}」が出典の quote と一致しない")
    return errs


def total_chars(script: dict) -> int:
    return sum(len(s["narration"]) for s in script["scenes"])


def generate(job: Job, topic: str | None, force=False, brief: str | None = None) -> dict:
    log = get_logger(job)
    if job.script.exists() and not force:
        log.info(f"既存の台本を使用: {job.script}")
        return load_json(job.script)
    prompt = build_prompt(job, topic)
    if brief:
        prompt += "\n\n# 追加指示(制作者から。上記のルールより具体的な場合はこちらを優先。ただし事実確認と禁止事項は必ず守る)\n" + brief
    (job.scripts / "prompt.md").write_text(prompt, encoding="utf-8")
    raw = call_llm(prompt, log)
    (job.scripts / "llm_raw.txt").write_text(raw, encoding="utf-8")
    script = extract_json(raw)
    errs = validate(script)
    if errs:
        log.warning("台本検証で問題: " + "; ".join(errs))
        fix = prompt + "\n\n# 前回の出力\n```json\n" + json.dumps(script, ensure_ascii=False) + \
            "\n```\n\n# 修正指示\n次の問題をすべて解消して、JSONを出し直してください:\n- " + "\n- ".join(errs)
        raw = call_llm(fix, log)
        (job.scripts / "llm_raw_fix.txt").write_text(raw, encoding="utf-8")
        script = extract_json(raw)
        errs = validate(script)
        if errs:
            script.setdefault("human_check", []).extend([f"[自動検証NG] {e}" for e in errs])
    script["job_id"] = job.id
    script["topic_request"] = topic
    save_json(job.script, script)
    log.info(f"台本: {len(script['scenes'])}シーン / {total_chars(script)}字 → {job.script}")
    job.mark("script", not errs, chars=total_chars(script), problems=errs)
    return script


def shorten(job: Job, script: dict, over_sec: float, cur_sec: float, log) -> dict:
    """音声の実測長が上限を超えた場合の調整。LLMで短縮 → 失敗時は optional シーンを削除。"""
    ratio = max(0.5, 1 - (over_sec + 1.0) / cur_sec)
    target = int(total_chars(script) * ratio)
    try:
        prompt = ("次のショート動画台本のナレーションを、事実・出典・発言の正確さを保ったまま合計"
                  f"{target}字以内に短縮してください。シーン構成とid、fact_ids、visual は維持し、narration と highlights だけ変更。"
                  "かぎかっこ内の発言は変更しないこと。JSON全体を ```json で出力。\n```json\n"
                  + json.dumps(script, ensure_ascii=False) + "\n```")
        new = extract_json(call_llm(prompt, log))
        if not validate(new) and total_chars(new) < total_chars(script):
            new["job_id"] = script.get("job_id")
            log.info(f"LLMで短縮: {total_chars(script)}字 → {total_chars(new)}字")
            return new
    except Exception as e:
        log.warning(f"LLM短縮に失敗: {e}")
    opt = [s for s in script["scenes"] if s.get("optional")]
    if opt:
        script["scenes"].remove(opt[-1])
        log.info(f"optional シーン {opt[-1]['id']} を削除して短縮")
        return script
    raise ScriptError("尺を短縮できません。台本を手動で短くしてください: " + str(job.script))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--job", required=True)
    ap.add_argument("--topic")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--brief", help="企画書(brief.md)のパス。台本生成の追加指示として渡す")
    a = ap.parse_args()
    b = open(a.brief, encoding="utf-8").read() if a.brief else None
    generate(Job(a.job), a.topic, a.force, brief=b)
