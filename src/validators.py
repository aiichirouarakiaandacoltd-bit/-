"""Status validation and completeness checking."""
import json
from datetime import datetime
from pathlib import Path

import config as cfg


REQUIRED_FILES = [
    "01_research_report.md",
    "02_narration_script.md",
    "03_editing_instructions.md",
    "04_materials_list.md",
    "05_posting_package.md",
    "06_bgm_and_credits.md",
    "07_ng_check_report.md",
    "08_bgm_plan.md",
    "09_package_summary.md",
    "metadata.json",
]


def check_zero_byte_files(output_dir):
    output_dir = Path(output_dir)
    zero_files = []
    for f in output_dir.iterdir():
        if f.is_file() and f.stat().st_size == 0:
            zero_files.append(f.name)
    return zero_files


def _is_blocking_fact(fact):
    if fact.get("blocking") is False or fact.get("required_for_content") is False:
        return False
    return True


def _determine_fact_check_status(all_facts, unconfirmed_facts):
    has_rejected = any(f.get("status") == "rejected" for f in all_facts)
    if has_rejected:
        return "failed"
    blocking_facts = [f for f in all_facts if _is_blocking_fact(f)]
    has_manual = any(f.get("manual_source_verification_required") for f in blocking_facts)
    has_unusable = any(not f.get("usable_in_script") for f in blocking_facts)
    has_unconfirmed = len(unconfirmed_facts) > 0
    if has_manual or has_unusable or has_unconfirmed:
        return "manual_verification_required"
    return "all_confirmed"


def _validate_bgm_config(bgm_config):
    """Check BGM configuration completeness for production readiness.

    Returns (issues, warnings) tuple. For contracted BGM with contract_evidence,
    verification items (contract_evidence_verified, content_id_status,
    local_file_verified) are warnings, not blocking issues.
    """
    issues = []
    warnings = []
    if not bgm_config.get("file_name"):
        issues.append("BGMファイル名が未設定")
    if not bgm_config.get("provider"):
        issues.append("BGM提供元が未設定")

    license_status = bgm_config.get("license_status", "")
    is_contracted = license_status == "contracted"
    has_evidence = bool(bgm_config.get("contract_evidence") or bgm_config.get("license_evidence"))

    if is_contracted:
        if not has_evidence:
            issues.append("契約証跡が未設定")
        if not bgm_config.get("credit_text"):
            issues.append("クレジット表記が未設定")
        if has_evidence:
            if not bgm_config.get("contract_evidence_verified"):
                warnings.append("契約証跡の実確認が未完了（荒木側で確認必要）")
            if not bgm_config.get("download_or_reference_url"):
                warnings.append("BGM参照URLが未設定（公開URLがない契約ファイルのため警告のみ）")
        else:
            if not bgm_config.get("contract_evidence_verified"):
                issues.append("契約証跡の実確認が未完了")
    else:
        if not bgm_config.get("download_or_reference_url"):
            issues.append("BGM正式参照URL未設定")

    if bgm_config.get("content_id_status", "unconfirmed") == "unconfirmed":
        if is_contracted and has_evidence:
            warnings.append("Content ID状態が未確認（荒木側で確認必要）")
        else:
            issues.append("Content ID状態が未確認")
    if not bgm_config.get("local_file_verified"):
        if is_contracted and has_evidence:
            warnings.append("BGMローカルファイルの検証が未完了（荒木側で確認必要）")
        else:
            issues.append("BGMローカルファイルの検証が未完了")
    return issues, warnings


def validate_package(output_dir, research_data, ng_results, bgm_config, topic,
                     topic_source="manual", mode="production", rights_data=None):
    output_dir = Path(output_dir)

    missing_files = []
    for fname in REQUIRED_FILES:
        fp = output_dir / fname
        if not fp.exists():
            missing_files.append(fname)

    zero_files = check_zero_byte_files(output_dir)

    generated_files = [f.name for f in output_dir.iterdir() if f.is_file()]

    fact_statuses = [f.get("status", "unconfirmed") for f in research_data.get("facts", [])]
    has_unconfirmed_in_script = False
    for f in research_data.get("facts", []):
        if f.get("status") in ("unconfirmed", "rejected") and f.get("usable_in_script"):
            has_unconfirmed_in_script = True

    ng_has_fail = False
    ng_has_review = False
    if ng_results:
        for finding in ng_results.get("findings", []):
            if finding.get("verdict") == "FAIL":
                ng_has_fail = True
            if finding.get("verdict") == "REVIEW":
                ng_has_review = True

    bgm_license = bgm_config.get("license_status", "")
    bgm_contracted = bgm_license == "contracted"
    bgm_url_configured = bool(bgm_config.get("download_or_reference_url"))

    if rights_data is None:
        rights_data = {}
    rights_overall = rights_data.get("overall_status", "REVIEW")
    rights_has_review = rights_data.get("has_review", False)
    bgm_issues, bgm_warnings = _validate_bgm_config(bgm_config)

    missing_items = list(missing_files)
    if zero_files:
        missing_items.append(f"0KBファイル: {', '.join(zero_files)}")
    if has_unconfirmed_in_script:
        missing_items.append("UNCONFIRMED/REJECTEDの事実が台本に混入の可能性")
    if ng_has_fail:
        missing_items.append("NG表現チェックにFAILあり")
    for issue in bgm_issues:
        missing_items.append(issue)

    unconfirmed_facts = [f for f in research_data.get("facts", [])
                         if f.get("status") in ("unconfirmed", "partial")
                         and _is_blocking_fact(f)]
    if unconfirmed_facts and mode == "production":
        missing_items.append(f"出典未確認の事実が{len(unconfirmed_facts)}件")

    all_facts = research_data.get("facts", [])
    unsourced_facts = [f for f in all_facts
                       if not f.get("source_url") and not f.get("resource_identifier")]
    unsourced_majority = len(unsourced_facts) > len(all_facts) / 2 if all_facts else False
    if unsourced_majority and mode == "production":
        missing_items.append(f"主要factの過半数({len(unsourced_facts)}/{len(all_facts)})が出典未設定")

    manual_verify_facts = [f for f in all_facts
                           if f.get("manual_source_verification_required")
                           and _is_blocking_fact(f)]
    if manual_verify_facts and mode == "production":
        missing_items.append(f"手動出典確認が必要なfactが{len(manual_verify_facts)}件")

    script_path = output_dir / "02_narration_script.md"
    shorts_broken = False
    script_not_narration = False
    credit_duplication = False
    if script_path.exists():
        script_content = script_path.read_text(encoding="utf-8")
        separator_lines = [l for l in script_content.split("\n")
                           if l.strip() and all(c == "=" for c in l.strip())]
        if len(separator_lines) > 5:
            shorts_broken = True
            missing_items.append("Shorts台本にヘッダー重複あり")
        if "出典確認後に" in script_content:
            script_not_narration = True
            if mode == "production":
                missing_items.append("台本がナレーション原稿になっていない（テンプレートのまま）")

    script_duration_short = False
    script_estimated_minutes = 0.0
    if script_path.exists():
        from src.script_writer import count_narration_chars, estimate_reading_minutes
        long_start = script_content.find("## 長尺台本")
        if long_start >= 0:
            shorts_start = script_content.find("---", long_start)
            long_text = script_content[long_start:shorts_start] if shorts_start >= 0 else script_content[long_start:]
            sep_pos = long_text.find("=" * 20)
            if sep_pos >= 0:
                narration_text = long_text[sep_pos:]
            else:
                narration_text = long_text
            char_count = count_narration_chars(narration_text)
            script_estimated_minutes = estimate_reading_minutes(char_count)
            target_min = cfg.NARRATION_TARGET_MIN_MINUTES
            target_max = cfg.NARRATION_TARGET_MAX_MINUTES
            if script_estimated_minutes < target_min and mode == "production":
                script_duration_short = True
                missing_items.append(
                    f"長尺台本が目標尺に未達（推定{script_estimated_minutes:.1f}分、"
                    f"目標{target_min}〜{target_max}分）"
                )

    shorts_duration_short = False
    shorts_01_estimated_seconds = 0.0
    shorts_02_estimated_seconds = 0.0
    shorts_03_estimated_seconds = 0.0
    if script_path.exists():
        s01_start = script_content.find("## Shorts 01 台本")
        s02_start = script_content.find("## Shorts 02 台本")
        s03_start = script_content.find("## Shorts 03 台本")
        if s01_start >= 0 and s02_start >= 0:
            min_shorts_sec = cfg.VIDEO_SPECS["shorts"]["duration_min_seconds"]
            shorts_sections = []
            if s03_start >= 0:
                shorts_sections = [
                    ("01", script_content[s01_start:s02_start]),
                    ("02", script_content[s02_start:s03_start]),
                    ("03", script_content[s03_start:]),
                ]
            else:
                shorts_sections = [
                    ("01", script_content[s01_start:s02_start]),
                    ("02", script_content[s02_start:]),
                ]
            for s_label, s_text in shorts_sections:
                sep = s_text.find("=" * 20)
                narr = s_text[sep:] if sep >= 0 else s_text
                c = count_narration_chars(narr)
                est_sec = estimate_reading_minutes(c) * 60
                if s_label == "01":
                    shorts_01_estimated_seconds = round(est_sec, 1)
                elif s_label == "02":
                    shorts_02_estimated_seconds = round(est_sec, 1)
                else:
                    shorts_03_estimated_seconds = round(est_sec, 1)
                if est_sec < min_shorts_sec:
                    shorts_duration_short = True
                    missing_items.append(
                        f"Shorts {s_label}が目標尺に未達"
                        f"（推定{est_sec:.1f}秒、最低{min_shorts_sec}秒）"
                    )

    if rights_has_review:
        missing_items.append("素材の権利REVIEWが未解決")

    posting_path = output_dir / "05_posting_package.md"
    if posting_path.exists():
        posting_content = posting_path.read_text(encoding="utf-8")
        import re as _re
        if _re.search(r"(\w+): \1:", posting_content):
            credit_duplication = True
            missing_items.append("クレジット二重表記あり")

    package_structure_complete = (
        len(missing_files) == 0
        and len(zero_files) == 0
    )

    usable_confirmed = [
        f for f in all_facts
        if f.get("status") == cfg.FactStatus.CONFIRMED
        and f.get("verified_excerpt")
        and f.get("usable_in_script")
    ]
    core_facts_confirmed = len(usable_confirmed) >= 2 if all_facts else False

    content_complete = (
        package_structure_complete
        and not ng_has_fail
        and not has_unconfirmed_in_script
        and not shorts_broken
        and not unsourced_majority
        and not script_not_narration
        and core_facts_confirmed
        and not script_duration_short
        and not shorts_duration_short
    )

    rights_ok = rights_overall == "OK"

    ng_check_ok = not ng_has_fail and not ng_has_review

    production_ready = (
        content_complete
        and len(bgm_issues) == 0
        and len(unconfirmed_facts) == 0
        and len(manual_verify_facts) == 0
        and not credit_duplication
        and rights_ok
        and ng_check_ok
        and mode == "production"
    )

    manual_review_required = (
        not production_ready
        or len(unconfirmed_facts) > 0
        or len(bgm_issues) > 0
        or rights_has_review
        or ng_has_review
    )

    is_test = mode == "test"

    status = {
        "project_name": "imperial-video-automation",
        "channel_name": cfg.CHANNEL_NAME,
        "topic": topic,
        "topic_source": topic_source,
        "mode": mode,
        "test_mode": is_test,
        "package_structure_complete": package_structure_complete,
        "content_complete": content_complete,
        "production_ready": production_ready if not is_test else False,
        "manual_review_required": manual_review_required,
        "fact_check_status": _determine_fact_check_status(all_facts, unconfirmed_facts),
        "rights_status": rights_overall.lower() if rights_overall else "review_required",
        "ng_check_status": "fail" if ng_has_fail else ("review_required" if ng_has_review else "pass"),
        "bgm_url_configured": bgm_url_configured,
        "bgm_contracted": bgm_contracted,
        "bgm_validation": "ok" if len(bgm_issues) == 0 else "incomplete",
        "bgm_issues": bgm_issues,
        "bgm_warnings": bgm_warnings,
        "script_estimated_minutes": round(script_estimated_minutes, 1),
        "shorts_01_estimated_seconds": shorts_01_estimated_seconds,
        "shorts_02_estimated_seconds": shorts_02_estimated_seconds,
        "shorts_03_estimated_seconds": shorts_03_estimated_seconds,
        "missing_items": missing_items,
        "generated_files": sorted(generated_files),
        "zero_byte_files": zero_files,
        "created_at": datetime.now().isoformat(),
    }

    if is_test:
        status["generated_for_test_only"] = True
        status["factual_verification_required"] = True

    return status


def write_status_json(status, output_dir):
    output_dir = Path(output_dir)
    path = output_dir / "metadata.json"
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def generate_package_summary(topic, research_data, ng_results, bgm_config,
                             status, output_dir):
    """Generate 09_package_summary.md."""
    output_dir = Path(output_dir)
    lines = []
    lines.append("# 制作パッケージ概要")
    lines.append("")
    lines.append(f"## 企画テーマ")
    lines.append(f"{topic}")
    lines.append("")
    lines.append(f"## チャンネル")
    lines.append(f"{status.get('channel_name', '日本が誇る皇室物語')}")
    lines.append("")
    lines.append(f"## モード")
    lines.append(f"{status.get('mode', 'unknown')}")
    lines.append("")

    lines.append("## パッケージ判定")
    lines.append("")
    lines.append(f"- package_structure_complete: {status.get('package_structure_complete')}")
    lines.append(f"- content_complete: {status.get('content_complete')}")
    lines.append(f"- production_ready: {status.get('production_ready')}")
    lines.append(f"- manual_review_required: {status.get('manual_review_required')}")
    lines.append("")

    missing = status.get("missing_items", [])
    if missing:
        lines.append("## 不足・要確認項目")
        lines.append("")
        for item in missing:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## 生成ファイル一覧")
    lines.append("")
    for f in status.get("generated_files", []):
        lines.append(f"- {f}")
    lines.append("")

    zero = status.get("zero_byte_files", [])
    if zero:
        lines.append("## 0KBファイル（禁止）")
        lines.append("")
        for f in zero:
            lines.append(f"- **{f}**")
        lines.append("")

    lines.append("## ファクトチェック状況")
    lines.append(f"{status.get('fact_check_status', '未実施')}")
    lines.append("")
    lines.append("## 推定尺")
    lines.append(f"- 長尺: 推定{status.get('script_estimated_minutes', 0)}分")
    lines.append(f"- Shorts 01: 推定{status.get('shorts_01_estimated_seconds', 0)}秒")
    lines.append(f"- Shorts 02: 推定{status.get('shorts_02_estimated_seconds', 0)}秒")
    if status.get('shorts_03_estimated_seconds', 0) > 0:
        lines.append(f"- Shorts 03: 推定{status.get('shorts_03_estimated_seconds', 0)}秒")
    lines.append("")
    lines.append("## 権利確認状況")
    lines.append(f"- rights_status: {status.get('rights_status', '未実施')}")
    lines.append("")
    lines.append("## NG表現チェック状況")
    lines.append(f"{status.get('ng_check_status', '未実施')}")
    lines.append("")
    lines.append("## BGM設定状況")
    if status.get("bgm_contracted"):
        lines.append("- ライセンス: contracted（契約済み）")
    lines.append(f"- URL設定: {'済' if status.get('bgm_url_configured') else '未設定（荒木側で設定必要）'}")
    lines.append(f"- BGM検証: {status.get('bgm_validation', '未実施')}")
    bgm_issues = status.get("bgm_issues", [])
    if bgm_issues:
        for issue in bgm_issues:
            lines.append(f"  - {issue}")
    bgm_warnings = status.get("bgm_warnings", [])
    if bgm_warnings:
        lines.append("- BGM警告（production_readyには影響しない）:")
        for w in bgm_warnings:
            lines.append(f"  - {w}")
    lines.append("")

    if status.get("test_mode"):
        lines.append("## テストモード注記")
        lines.append("")
        lines.append("- このパッケージはテスト動作確認用です")
        lines.append("- production_ready = false")
        lines.append("- 出典の事実確認が必要です")
        lines.append("")

    lines.append("## 荒木側で確認すべき項目")
    lines.append("")
    lines.append("- 出典の最終確認")
    lines.append("- 外注者へ渡す前の内容確認")
    lines.append("- 素材URLの権利確認")
    lines.append("- BGM正式URLの設定（未設定の場合）")
    lines.append("")

    lines.append(f"生成日時: {status.get('created_at', '')}")

    content = "\n".join(lines)
    (output_dir / "09_package_summary.md").write_text(content, encoding="utf-8")
