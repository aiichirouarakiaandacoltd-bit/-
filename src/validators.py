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
]


def check_zero_byte_files(output_dir):
    output_dir = Path(output_dir)
    zero_files = []
    for f in output_dir.iterdir():
        if f.is_file() and f.stat().st_size == 0:
            zero_files.append(f.name)
    return zero_files


def _validate_bgm_config(bgm_config):
    """Check BGM configuration completeness for production readiness."""
    issues = []
    if not bgm_config.get("download_or_reference_url"):
        issues.append("BGM正式参照URL未設定")
    if not bgm_config.get("file_name"):
        issues.append("BGMファイル名が未設定")
    if not bgm_config.get("provider"):
        issues.append("BGM提供元が未設定")
    return issues


def validate_package(output_dir, research_data, ng_results, bgm_config, topic,
                     topic_source="manual", mode="production"):
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
    if ng_results:
        for finding in ng_results.get("findings", []):
            if finding.get("verdict") == "FAIL":
                ng_has_fail = True

    bgm_url_configured = bool(bgm_config.get("download_or_reference_url"))
    bgm_issues = _validate_bgm_config(bgm_config)

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
                         if f.get("status") in ("unconfirmed", "partial")]
    if unconfirmed_facts and mode == "production":
        missing_items.append(f"出典未確認の事実が{len(unconfirmed_facts)}件")

    all_facts = research_data.get("facts", [])
    unsourced_facts = [f for f in all_facts
                       if not f.get("source_url") and not f.get("resource_identifier")]
    unsourced_majority = len(unsourced_facts) > len(all_facts) / 2 if all_facts else False
    if unsourced_majority and mode == "production":
        missing_items.append(f"主要factの過半数({len(unsourced_facts)}/{len(all_facts)})が出典未設定")

    manual_verify_facts = [f for f in all_facts if f.get("manual_source_verification_required")]
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

    posting_path = output_dir / "05_posting_package.md"
    if posting_path.exists():
        posting_content = posting_path.read_text(encoding="utf-8")
        import re as _re
        if _re.search(r"(\w+): \1:", posting_content):
            credit_duplication = True
            missing_items.append("クレジット二重表記あり")

    package_complete = (
        len(missing_files) == 0
        and len(zero_files) == 0
        and not ng_has_fail
        and not has_unconfirmed_in_script
        and not shorts_broken
        and not unsourced_majority
    )

    production_ready = (
        package_complete
        and bgm_url_configured
        and len(bgm_issues) == 0
        and len(unconfirmed_facts) == 0
        and not script_not_narration
        and not credit_duplication
        and mode == "production"
    )

    manual_review_required = (
        not production_ready
        or len(unconfirmed_facts) > 0
        or len(bgm_issues) > 0
    )

    is_test = mode == "test"

    status = {
        "project_name": "imperial-video-automation",
        "channel_name": cfg.CHANNEL_NAME,
        "topic": topic,
        "topic_source": topic_source,
        "mode": mode,
        "test_mode": is_test,
        "package_complete": package_complete,
        "production_ready": production_ready if not is_test else False,
        "manual_review_required": manual_review_required,
        "fact_check_status": "all_confirmed" if not unconfirmed_facts else "review_needed",
        "rights_status": "ok",
        "ng_check_status": "fail" if ng_has_fail else "pass",
        "bgm_url_configured": bgm_url_configured,
        "bgm_validation": "ok" if len(bgm_issues) == 0 else "incomplete",
        "bgm_issues": bgm_issues,
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
    lines.append(f"- package_complete: {status.get('package_complete')}")
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
    lines.append("## NG表現チェック状況")
    lines.append(f"{status.get('ng_check_status', '未実施')}")
    lines.append("")
    lines.append("## BGM設定状況")
    lines.append(f"- URL設定: {'済' if status.get('bgm_url_configured') else '未設定（荒木側で設定必要）'}")
    lines.append(f"- BGM検証: {status.get('bgm_validation', '未実施')}")
    bgm_issues = status.get("bgm_issues", [])
    if bgm_issues:
        for issue in bgm_issues:
            lines.append(f"  - {issue}")
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
