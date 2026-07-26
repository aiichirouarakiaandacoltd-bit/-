"""承認用サマリー・監査ファイルへの機械記入.

集計するのは機械的に数えられる事項のみである。
リスクの評価、判断項目の文面、総合判定はサブエージェントと荒木愛一朗が書く。
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from . import id_assigner, scaffold

ENC = "utf-8"

# 第14章の不明情報タグ
UNCONFIRMED_TAGS = (
    "【未確認】", "【一次資料未確認】", "【権利条件要確認】", "【素材URL未取得】",
    "【人物確認が必要】", "【日付確認が必要】", "【使用非推奨】", "【アクセス未確認】",
)

# 架空URLとみなすホスト・語
FAKE_URL_MARKERS = ("example.com", "example.org", "example.net", "dummy.", "架空", "サンプルURL")

_URL = re.compile(r"https?://[^\s|,、）\)\]】\"']+")


# ---------------------------------------------------------------------
# 集計
# ---------------------------------------------------------------------
def fact_stats(fact_rows: list[dict]) -> dict:
    states = Counter((row.get("確認状態") or "未記入").strip() or "未記入" for row in fact_rows)
    kinds = Counter((row.get("分類") or "未記入").strip() or "未記入" for row in fact_rows)
    confirmed = states.get("確認済み", 0) + states.get("複数資料で確認済み", 0)
    return {
        "total": len(fact_rows),
        "confirmed": confirmed,
        "needs_check": states.get("要追加確認", 0) + states.get("一次資料未確認", 0),
        "unusable": states.get("使用不可", 0),
        "states": dict(states),
        "kinds": dict(kinds),
    }


def material_stats(material_rows: list[dict], long_visual_rows: list[dict]) -> dict:
    usage = Counter((row.get("YouTube利用可否") or "未記入").strip() or "未記入" for row in material_rows)
    states = Counter((row.get("確認状態") or "未記入").strip() or "未記入" for row in material_rows)
    shortage = sum(
        1 for row in long_visual_rows
        if (row.get("素材種別") or "").strip() == "素材不足"
    )
    return {
        "total": len(material_rows),
        "usable": usage.get("使用可", 0) + usage.get("条件付き使用可", 0),
        "needs_check": usage.get("要確認", 0),
        "not_recommended": usage.get("使用非推奨", 0),
        "forbidden": usage.get("使用禁止", 0),
        "usage": dict(usage),
        "states": dict(states),
        "shortage_rows": shortage,
        "visual_rows": len(long_visual_rows),
    }


def count_unconfirmed_tags(project_root: Path) -> dict:
    counts: Counter = Counter()
    for path in sorted(Path(project_root).rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".md", ".csv"):
            continue
        if "_history" in path.parts or "FINAL_EDITOR_PACKAGE" in path.parts:
            continue
        encoding = "utf-8-sig" if path.suffix.lower() == ".csv" else ENC
        try:
            text = path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        for tag in UNCONFIRMED_TAGS:
            found = text.count(tag)
            if found:
                counts[tag] += found
    return dict(counts)


def find_fake_urls(project_root: Path) -> list[str]:
    """架空URLの疑いがあるものを列挙する."""
    found: list[str] = []
    for relative in ("research/04_出典一覧.csv", "research/06_素材権利台帳.csv",
                     "production/12_長尺素材設計.csv", "production/16_投稿設定.md"):
        path = Path(project_root) / relative
        if not path.exists():
            continue
        encoding = "utf-8-sig" if path.suffix.lower() == ".csv" else ENC
        text = path.read_text(encoding=encoding)
        for url in _URL.findall(text):
            if any(marker in url for marker in FAKE_URL_MARKERS):
                entry = f"{relative}: {url}"
                if entry not in found:
                    found.append(entry)
    return found


def find_ai_face_materials(material_rows: list[dict]) -> list[str]:
    """皇族方のAI生成顔・顔加工素材の疑いがある行を検出する."""
    keywords = ("AI生成", "AI画像", "生成画像", "顔合成", "顔の合成", "ディープフェイク",
                "若返", "老化", "加工した顔", "合成写真")
    flagged: list[str] = []
    for row in material_rows:
        blob = " ".join(str(value or "") for value in row.values())
        person = (row.get("人物") or "").strip()
        if not any(keyword in blob for keyword in keywords):
            continue
        if person and person not in ("なし", "-", "無し"):
            flagged.append(
                f"{(row.get('素材ID') or '?').strip()}：{(row.get('素材内容') or '').strip()}（人物：{person}）"
            )
    return flagged


# ---------------------------------------------------------------------
# 機械記入ブロックの本文生成
# ---------------------------------------------------------------------
def fact_stats_markdown(stats: dict) -> str:
    lines = [
        "| 区分 | 件数 |",
        "| --- | --- |",
        f"| 事実台帳の総数 | {stats['total']} |",
        f"| 確認済み（確認済み＋複数資料で確認済み） | {stats['confirmed']} |",
        f"| 要確認（要追加確認＋一次資料未確認） | {stats['needs_check']} |",
        f"| 使用不可 | {stats['unusable']} |",
    ]
    if stats["states"]:
        lines.append("")
        lines.append("確認状態の内訳：" + "／".join(
            f"{key} {value}件" for key, value in sorted(stats["states"].items())
        ))
    if stats["total"] == 0:
        lines.append("")
        lines.append("> 事実台帳が未記入である。工程4を実行すること。")
    return "\n".join(lines)


def material_stats_markdown(stats: dict) -> str:
    lines = [
        "| 区分 | 件数 |",
        "| --- | --- |",
        f"| 素材候補数 | {stats['total']} |",
        f"| 使用可・条件付き使用可 | {stats['usable']} |",
        f"| 要確認 | {stats['needs_check']} |",
        f"| 使用非推奨 | {stats['not_recommended']} |",
        f"| 使用禁止 | {stats['forbidden']} |",
        f"| 長尺素材設計の行数 | {stats['visual_rows']} |",
        f"| うち「素材不足」の行 | {stats['shortage_rows']} |",
    ]
    if stats["total"] == 0:
        lines.append("")
        lines.append("> 素材権利台帳が未記入である。工程5を実行すること。")
    return "\n".join(lines)


def risk_flags_markdown(flags: dict) -> str:
    lines = ["**機械検出フラグ**", ""]
    if not any(flags.values()):
        lines.append("- 機械的に検出されたフラグはない。")
        return "\n".join(lines)

    if flags.get("forbidden_blocking"):
        lines.append(f"- 禁止表現（使用禁止相当）：{flags['forbidden_blocking']}件 → `audit/00_機械検出レポート.md` を参照")
    if flags.get("forbidden_review"):
        lines.append(f"- 禁止表現（要文脈確認）：{flags['forbidden_review']}件")
    if flags.get("required_missing"):
        lines.append(f"- 必須項目の欠落：{flags['required_missing']}件")
    if flags.get("unusable_facts"):
        lines.append(f"- **台本が「使用不可」の事実を参照している：{', '.join(flags['unusable_facts'])}**（最終版生成をブロックする）")
    if flags.get("missing_facts"):
        lines.append(f"- 台本が参照する事実IDが台帳に無い：{', '.join(flags['missing_facts'])}")
    if flags.get("unusable_materials"):
        lines.append(f"- 使用できない素材を参照している：{', '.join(flags['unusable_materials'])}")
    if flags.get("fake_urls"):
        lines.append("- **架空URLの疑い**：")
        lines.extend(f"    - {item}" for item in flags["fake_urls"])
    if flags.get("ai_face"):
        lines.append("- **皇族方のAI生成顔・顔加工素材の疑い**：")
        lines.extend(f"    - {item}" for item in flags["ai_face"])
    if flags.get("script_mismatch"):
        lines.append(f"- **長尺台本 10A と 10B の本文が一致しない**：{flags['script_mismatch']}")
    if flags.get("unresolved_settings"):
        lines.append("- 設定値が未入力のまま成果物へ出ている：")
        lines.extend(f"    - {item}" for item in flags["unresolved_settings"])
    if flags.get("honorifics"):
        lines.append("- 敬称の表記ゆれ候補：")
        lines.extend(f"    - {item}" for item in flags["honorifics"])
    if flags.get("tags"):
        lines.append("- 未確認タグの出現数：" + "／".join(
            f"{tag} {count}件" for tag, count in sorted(flags["tags"].items())
        ))
    if flags.get("char_count") is not None:
        lines.append(
            f"- 長尺台本の文字数：{flags['char_count']}字"
            f"（目標 {flags.get('char_target', '')}）"
        )
    return "\n".join(lines)


def compare_script_bodies(project_root: Path) -> dict:
    """10A（監査用）と10B（編集者用）の本文が一致しているか検査する.

    両者はIDの有無だけが異なり、本文の文言は同一でなければならない。
    片方だけを直したまま気付かない事故を防ぐための機械検査である。
    """
    project_root = Path(project_root)
    audit_path = project_root / "scripts" / "10A_長尺台本_監査用.md"
    editor_path = project_root / "scripts" / "10B_長尺台本_編集者用.md"

    if not audit_path.exists() or not editor_path.exists():
        return {"status": "判定不能（台本が未生成）", "match": None, "detail": ""}

    def _body(path: Path, end_marker: str) -> str:
        text = path.read_text(encoding=ENC)
        if "## 本編" not in text or end_marker not in text:
            return ""
        body = text[text.index("## 本編"):text.index(end_marker)]
        body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
        body = re.sub(r"【(事実|素材)ID[：:][^】]*】", "", body)
        body = re.sub(r"^\*\*参考情報\*\*[：:].*$", "", body, flags=re.MULTILINE)
        body = re.sub(r"^>.*$", "", body, flags=re.MULTILINE)
        return re.sub(r"\s+", "", body)

    audit_body = _body(audit_path, "## 使用した事実IDの一覧")
    editor_body = _body(editor_path, "## 読み方注記")

    if not audit_body and not editor_body:
        return {"status": "判定不能（本文が未記入）", "match": None, "detail": ""}
    if audit_body == editor_body:
        return {"status": "一致", "match": True, "detail": f"本文 {len(audit_body)}字"}

    detail = f"10A {len(audit_body)}字 / 10B {len(editor_body)}字"
    for index, (left, right) in enumerate(zip(audit_body, editor_body)):
        if left != right:
            detail += (f"／最初の差異は {index} 文字目付近："
                       f"10A「…{audit_body[max(0, index - 20):index + 20]}…」")
            break
    return {"status": "不一致", "match": False, "detail": detail}


def find_unresolved_settings(project_root: Path) -> list[str]:
    """設定値が未入力のまま成果物へ出ている箇所を検出する.

    bgm_credit や contact が初期値のままだと、
    クレジット表記や問い合わせ先が欠けた状態で編集者へ渡ってしまう。
    """
    markers = {
        "【要確認・正式表記を荒木が入力】": "BGMクレジット（config/settings.yaml の bgm_credit）",
        "【お問い合わせ先：要入力】": "問い合わせ先（config/settings.yaml の contact）",
    }
    found: list[str] = []
    for relative in ("production/16_投稿設定.md", "production/17_編集者向け制作指示書.md"):
        path = Path(project_root) / relative
        if not path.exists():
            continue
        text = path.read_text(encoding=ENC)
        for marker, label in markers.items():
            if marker in text:
                entry = f"{label} … {relative} に未入力のまま残っている"
                if entry not in found:
                    found.append(entry)
    return found


def count_script_chars(script_path: Path) -> int:
    """台本本文の文字数を数える（見出し・表・注記・IDタグを除く）."""
    path = Path(script_path)
    if not path.exists():
        return 0
    text = path.read_text(encoding=ENC)
    body = text
    match = re.search(r"^##\s*本編\s*$(.*?)^##\s", text, re.MULTILINE | re.DOTALL)
    if match:
        body = match.group(1)
    body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
    body = re.sub(r"【(事実|素材)ID[：:][^】]*】", "", body)
    lines = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        # 見出し・表・引用・コードフェンスは読み上げ対象外
        if stripped.startswith(("#", "|", ">", "```")):
            continue
        # 箇条書きは「記号＋空白」の形のみ除外する。
        # 「**発言は確認できていません。**」のような太字始まりの
        # ナレーション行を箇条書きと誤認しないため。
        if re.match(r"^([-*+]\s|\d+[.)]\s)", stripped):
            continue
        # テンプレートの指示文（丸かっこで囲まれた行）は除外する
        if stripped.startswith("（") and stripped.endswith("）"):
            continue
        lines.append(stripped)
    joined = "".join(lines)
    # 強調記号は読み上げられないため、計数前に取り除く
    joined = re.sub(r"\*\*|__|(?<!\*)\*(?!\*)", "", joined)
    joined = re.sub(r"\s", "", joined)
    return len(joined)


# ---------------------------------------------------------------------
# 反映
# ---------------------------------------------------------------------
def update_summary(project_root: Path, fact_rows: list[dict], material_rows: list[dict],
                   long_visual_rows: list[dict], flags: dict, log=None) -> dict:
    """19_荒木承認用サマリー.md と 18_最終監査結果.md の機械ブロックを更新する."""
    project_root = Path(project_root)
    facts = fact_stats(fact_rows)
    materials = material_stats(material_rows, long_visual_rows)

    summary_path = project_root / "audit" / "19_荒木承認用サマリー.md"
    audit_path = project_root / "audit" / "18_最終監査結果.md"

    updated = []
    if scaffold.update_machine_block(summary_path, "fact_stats", fact_stats_markdown(facts)):
        updated.append("fact_stats")
    if scaffold.update_machine_block(summary_path, "material_stats", material_stats_markdown(materials)):
        updated.append("material_stats")
    if scaffold.update_machine_block(summary_path, "risk_flags", risk_flags_markdown(flags)):
        updated.append("risk_flags")

    audit_body = "\n".join([
        "**機械検出の要約**（詳細は `audit/00_機械検出レポート.md`）",
        "",
        fact_stats_markdown(facts),
        "",
        material_stats_markdown(materials),
        "",
        risk_flags_markdown(flags),
    ])
    if scaffold.update_machine_block(audit_path, "audit_summary", audit_body):
        updated.append("audit_summary")

    if log:
        log.info(f"機械記入ブロックを更新: {', '.join(updated) if updated else 'なし'}")

    return {"facts": facts, "materials": materials, "updated_blocks": updated}


def build_machine_report(project_root: Path, forbidden_result, required_result,
                         duplication_result: dict, cross_check: dict, flags: dict,
                         generated_at: str, sample_mode: bool) -> str:
    """audit/00_機械検出レポート.md の本文を作る."""
    banner = scaffold.SAMPLE_BANNER + "\n\n" if sample_mode else ""
    lines = [
        f"<!-- generated_at: {generated_at} -->",
        banner + "# 機械検出レポート",
        "",
        f"- 生成日時：{generated_at}",
        "- 生成元：run_imperial_pipeline.py（機械処理のみ）",
        "",
        "> このレポートは機械検出の結果である。**判定ではない。**",
        "> 事実判定・表現判定はサブエージェントと荒木愛一朗が行う。",
        "",
        "## 1. 必須項目の欠落検出",
        "",
        required_result.to_markdown(),
        "",
        "## 2. 禁止表現の検出",
        "",
        forbidden_result.to_markdown(),
        "",
        "## 3. 既存動画との重複（機械参考判定）",
        "",
        f"- 判定：{duplication_result.get('status')}",
        f"- 備考：{duplication_result.get('note', '')}",
        "",
        "## 4. 台本と台帳の突合",
        "",
    ]

    def _listing(title: str, values: list) -> None:
        lines.append(f"- {title}：{('、'.join(values) if values else 'なし')}")

    _listing("台本が参照する事実ID", cross_check.get("referenced_facts", []))
    _listing("台本が参照する素材ID", cross_check.get("referenced_materials", []))
    _listing("台帳に存在しない事実ID", cross_check.get("missing_facts", []))
    _listing("台帳に存在しない素材ID", cross_check.get("missing_materials", []))
    _listing("**確認状態が「使用不可」の事実を参照**", cross_check.get("unusable_facts", []))
    _listing("追加確認が必要な事実の参照", cross_check.get("needs_more_check", []))
    _listing("使用できない素材の参照", cross_check.get("unusable_materials", []))
    _listing("台本で未使用の事実ID", cross_check.get("unused_facts", []))
    compare = flags.get("script_compare") or {}
    if compare:
        lines.append(f"- 10A と 10B の本文一致：{compare.get('status', '未検査')}"
                     f"{'（' + compare['detail'] + '）' if compare.get('detail') else ''}")

    lines.extend([
        "",
        "## 5. 重大リスクのフラグ",
        "",
        risk_flags_markdown(flags),
        "",
        "## 6. 未確認タグの集計",
        "",
    ])
    tags = flags.get("tags") or {}
    if tags:
        lines.append("| タグ | 出現数 |")
        lines.append("| --- | --- |")
        lines.extend(f"| {tag} | {count} |" for tag, count in sorted(tags.items()))
    else:
        lines.append("未確認タグは検出されなかった。")

    return "\n".join(lines)
