"""
Report generation module for showa-heisei-video-automation.
Generates all text output files: descriptions, hashtags, summaries, credits, and status.
"""

import json
import subprocess
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# デフォルトハッシュタグ (全動画共通)
BASE_HASHTAGS = [
    "#昭和",
    "#平成",
    "#なぜそうだったのか",
    "#昭和レトロ",
    "#懐かしい",
]

# トピック別追加ハッシュタグ
TOPIC_HASHTAG_MAP: dict[str, list[str]] = {
    "テレビ": ["#ブラウン管テレビ", "#昭和のテレビ", "#テレビの歴史"],
    "電話": ["#黒電話", "#ダイヤル式電話", "#昭和の電話"],
    "布": ["#テレビカバー", "#レースの敷物", "#昭和の暮らし"],
    "食": ["#昭和の食卓", "#懐かしの味", "#昭和グルメ"],
    "学校": ["#昭和の学校", "#懐かしの学校", "#昭和の教育"],
    "遊び": ["#昭和の遊び", "#懐かしの遊び", "#昭和の子供"],
    "家電": ["#昭和の家電", "#三種の神器", "#レトロ家電"],
    "交通": ["#昭和の交通", "#懐かしの乗り物", "#昭和の街"],
    "文化": ["#昭和文化", "#昭和の暮らし", "#日本文化"],
}

# 固定コメントテンプレート
FIXED_COMMENT_TEMPLATE = """ご視聴いただきありがとうございます。

この動画は「{topic}」について、当時の資料や文献をもとに制作しました。

【参考資料・出典】
{sources_text}

内容に誤りや補足がございましたら、コメント欄でお知らせいただけると幸いです。
皆さまの思い出やエピソードもぜひお聞かせください。

※この動画の音声はVOICEVOXを使用しています。
※BGMはライセンスに基づき使用しています。

チャンネル登録・高評価いただけると励みになります。"""


def get_git_commit() -> str:
    """現在のgitコミットハッシュを取得する。

    Returns:
        コミットハッシュの短縮形。取得できない場合は "unknown"。
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    logger.warning("gitコミットハッシュの取得に失敗しました")
    return "unknown"


def generate_description(
    topic: str,
    sources: list[dict[str, str]],
    credits: list[str],
    hashtags: list[str],
    output_path: str,
) -> str:
    """YouTube動画の概要欄テキストを生成する。

    Args:
        topic: 動画のトピック。
        sources: 出典リスト。各要素は {"title": "...", "url": "..."} の辞書。
            URLが空や偽のものは除外される。
        credits: クレジット文のリスト。
        hashtags: ハッシュタグのリスト。
        output_path: 出力ファイルのパス。

    Returns:
        生成された概要欄テキスト。
    """
    lines: list[str] = []

    # タイトル・導入
    lines.append(f"「{topic}」について、当時の背景や理由を解説します。")
    lines.append("")

    # 出典
    valid_sources = _filter_valid_sources(sources)
    if valid_sources:
        lines.append("【参考資料・出典】")
        for src in valid_sources:
            title = src.get("title", "")
            url = src.get("url", "")
            if url:
                lines.append(f"・{title}: {url}")
            else:
                lines.append(f"・{title}")
        lines.append("")

    # クレジット
    if credits:
        lines.append("【クレジット】")
        for credit in credits:
            lines.append(f"・{credit}")
        lines.append("")

    # VOICEVOXクレジット
    lines.append("【音声】")
    lines.append("・VOICEVOX (https://voicevox.hiroshiba.jp/)")
    lines.append("")

    # ハッシュタグ
    if hashtags:
        lines.append(" ".join(hashtags))

    description_text = "\n".join(lines)

    _write_text_file(output_path, description_text)
    logger.info("概要欄テキストを出力しました: %s", output_path)

    return description_text


def _filter_valid_sources(sources: list[dict[str, str]]) -> list[dict[str, str]]:
    """実際に使用された有効な出典のみをフィルタリングする。

    偽のURL、プレースホルダー、空のエントリは除外する。
    """
    invalid_patterns = [
        "example.com",
        "placeholder",
        "dummy",
        "test",
        "xxx",
        "yyy",
        "zzz",
        "hogehoge",
        "fugafuga",
    ]

    valid: list[dict[str, str]] = []
    for src in sources:
        title = src.get("title", "").strip()
        url = src.get("url", "").strip()

        if not title:
            continue

        # URLが偽でないかチェック
        if url:
            url_lower = url.lower()
            is_fake = any(pattern in url_lower for pattern in invalid_patterns)
            if is_fake:
                logger.warning("偽のURLを除外しました: %s", url)
                # URLは除外するがタイトルは残す
                valid.append({"title": title, "url": ""})
                continue

        valid.append(src)

    return valid


def generate_fixed_comment(
    topic: str,
    sources: list[dict[str, str]],
    output_path: str,
) -> str:
    """固定コメント用テキストを生成する。

    Args:
        topic: 動画のトピック。
        sources: 出典リスト。
        output_path: 出力ファイルのパス。

    Returns:
        生成された固定コメントテキスト。
    """
    valid_sources = _filter_valid_sources(sources)
    if valid_sources:
        source_lines = []
        for src in valid_sources:
            title = src.get("title", "")
            url = src.get("url", "")
            if url:
                source_lines.append(f"・{title}: {url}")
            else:
                source_lines.append(f"・{title}")
        sources_text = "\n".join(source_lines)
    else:
        sources_text = "・各種公開資料を参考にしています"

    comment_text = FIXED_COMMENT_TEMPLATE.format(
        topic=topic,
        sources_text=sources_text,
    )

    _write_text_file(output_path, comment_text)
    logger.info("固定コメントテキストを出力しました: %s", output_path)

    return comment_text


def generate_hashtags(
    topic: str,
    output_path: str,
) -> list[str]:
    """ハッシュタグリストを生成する。

    基本ハッシュタグにトピック固有のタグを追加する。

    Args:
        topic: 動画のトピック。
        output_path: 出力ファイルのパス。

    Returns:
        ハッシュタグのリスト。
    """
    hashtags = list(BASE_HASHTAGS)

    # トピックに対応する追加ハッシュタグを検索
    for keyword, extra_tags in TOPIC_HASHTAG_MAP.items():
        if keyword in topic:
            for tag in extra_tags:
                if tag not in hashtags:
                    hashtags.append(tag)

    # トピック自体をハッシュタグに追加 (重複チェック)
    topic_tag = f"#{topic.replace(' ', '').replace('　', '')}"
    if topic_tag not in hashtags and len(topic_tag) <= 30:
        hashtags.append(topic_tag)

    hashtag_text = "\n".join(hashtags)
    _write_text_file(output_path, hashtag_text)
    logger.info("ハッシュタグを出力しました: %s (%d個)", output_path, len(hashtags))

    return hashtags


def generate_summary(
    status: dict[str, Any],
    output_path: str,
) -> str:
    """人間が読みやすいMarkdown形式のサマリーを生成する。

    Args:
        status: パイプライン全体のステータス辞書。
        output_path: 出力ファイルのパス。

    Returns:
        生成されたMarkdownテキスト。
    """
    lines: list[str] = []

    topic = status.get("topic", "不明")
    mode = status.get("mode", "不明")
    timestamp = status.get("timestamp", datetime.now().isoformat())

    lines.append(f"# 実行サマリー: {topic}")
    lines.append("")
    lines.append(f"- **実行日時**: {timestamp}")
    lines.append(f"- **モード**: {mode}")
    lines.append(f"- **gitコミット**: {status.get('git_commit', get_git_commit())}")
    lines.append("")

    # VOICEVOX情報
    voicevox = status.get("voicevox", {})
    lines.append("## 音声 (VOICEVOX)")
    lines.append("")
    lines.append(f"- **話者**: {voicevox.get('speaker', '不明')}")
    lines.append(f"- **スタイル**: {voicevox.get('style', '不明')}")
    lines.append(f"- **速度**: {voicevox.get('speed', '不明')}")
    lines.append("")

    # BGM情報
    bgm = status.get("bgm", {})
    lines.append("## BGM")
    lines.append("")
    lines.append(f"- **ファイル**: {bgm.get('file', '不明')}")
    lines.append(f"- **ライセンス**: {bgm.get('license', '不明')}")
    lines.append("")

    # ファクトチェック
    facts = status.get("facts", {})
    lines.append("## ファクトチェック")
    lines.append("")
    if isinstance(facts, dict):
        lines.append(f"- **確認済み**: {facts.get('confirmed', 0)}件")
        lines.append(f"- **部分確認**: {facts.get('partial', 0)}件")
        lines.append(f"- **未確認**: {facts.get('unconfirmed', 0)}件")
        lines.append(f"- **却下**: {facts.get('rejected', 0)}件")
    elif isinstance(facts, list):
        from collections import Counter
        counts = Counter(f.get("status", "不明") for f in facts)
        for fact_status, count in counts.items():
            lines.append(f"- **{fact_status}**: {count}件")
    lines.append("")

    # 素材情報
    materials = status.get("materials", {})
    lines.append("## 素材")
    lines.append("")
    if isinstance(materials, dict):
        lines.append(f"- **OK**: {materials.get('ok', 0)}件")
        lines.append(f"- **REVIEW**: {materials.get('review', 0)}件")
        lines.append(f"- **NG**: {materials.get('ng', 0)}件")
    elif isinstance(materials, list):
        from collections import Counter
        counts = Counter(m.get("status", "不明") for m in materials)
        for mat_status, count in counts.items():
            lines.append(f"- **{mat_status}**: {count}件")
    lines.append("")

    # 品質チェック結果
    quality = status.get("quality", {})
    lines.append("## 品質チェック")
    lines.append("")
    if isinstance(quality, dict):
        overall = quality.get("overall_pass", False)
        lines.append(f"- **結果**: {'PASS' if overall else 'FAIL'}")
        passed = quality.get("passed_checks", 0)
        total = quality.get("total_checks", 0)
        lines.append(f"- **合格**: {passed}/{total}")

        # 失敗チェックの詳細
        check_results = quality.get("results", [])
        failed = [r for r in check_results if not r.get("passed", True)]
        if failed:
            lines.append("")
            lines.append("### 失敗したチェック")
            lines.append("")
            for r in failed:
                severity_mark = "!!!" if r.get("severity") == "error" else "!"
                lines.append(
                    f"- [{severity_mark}] {r.get('check_name', '不明')}: "
                    f"{r.get('details', '詳細なし')}"
                )
    lines.append("")

    # 最終判定
    overall_pass = status.get("overall_pass", False)
    lines.append("## 最終判定")
    lines.append("")
    lines.append(f"**{'PASS - 公開可能' if overall_pass else 'FAIL - 要確認'}**")
    lines.append("")

    summary_text = "\n".join(lines)
    _write_text_file(output_path, summary_text)
    logger.info("サマリーを出力しました: %s", output_path)

    return summary_text


def generate_status_json(
    mode: str,
    topic: str,
    voicevox_info: dict[str, Any],
    bgm_info: dict[str, Any],
    facts_info: dict[str, Any],
    materials_info: dict[str, Any],
    quality_info: dict[str, Any],
    output_path: str,
) -> dict[str, Any]:
    """機械可読なステータスJSONを生成する。

    Args:
        mode: 実行モード ("production" or "test")。
        topic: トピック名。
        voicevox_info: VOICEVOX情報 (speaker, style, speed)。
        bgm_info: BGM情報 (file, license)。
        facts_info: ファクトチェック結果 (confirmed/partial/unconfirmed/rejected counts)。
        materials_info: 素材情報 (ok/review/ng counts)。
        quality_info: 品質チェック結果。
        output_path: 出力ファイルのパス。

    Returns:
        生成されたステータス辞書。
    """
    # ファクトチェックのカウント集計
    if isinstance(facts_info, list):
        facts_counts = {
            "confirmed": sum(1 for f in facts_info if f.get("status") == "CONFIRMED"),
            "partial": sum(1 for f in facts_info if f.get("status") == "PARTIAL"),
            "unconfirmed": sum(1 for f in facts_info if f.get("status") == "UNCONFIRMED"),
            "rejected": sum(1 for f in facts_info if f.get("status") == "REJECTED"),
        }
    else:
        facts_counts = {
            "confirmed": facts_info.get("confirmed", 0),
            "partial": facts_info.get("partial", 0),
            "unconfirmed": facts_info.get("unconfirmed", 0),
            "rejected": facts_info.get("rejected", 0),
        }

    # 素材のカウント集計
    if isinstance(materials_info, list):
        materials_counts = {
            "ok": sum(1 for m in materials_info if m.get("status") == "OK"),
            "review": sum(1 for m in materials_info if m.get("status") == "REVIEW"),
            "ng": sum(1 for m in materials_info if m.get("status") == "NG"),
        }
    else:
        materials_counts = {
            "ok": materials_info.get("ok", 0),
            "review": materials_info.get("review", 0),
            "ng": materials_info.get("ng", 0),
        }

    # 全体判定
    quality_pass = quality_info.get("overall_pass", False) if isinstance(quality_info, dict) else False
    facts_ok = facts_counts["rejected"] == 0 and facts_counts["unconfirmed"] == 0
    materials_ok = materials_counts["review"] == 0 and materials_counts["ng"] == 0
    overall_pass = quality_pass and facts_ok and materials_ok

    status_data: dict[str, Any] = {
        "mode": mode,
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "git_commit": get_git_commit(),
        "voicevox": {
            "speaker": voicevox_info.get("speaker", "不明"),
            "style": voicevox_info.get("style", "不明"),
            "speed": voicevox_info.get("speed", 1.0),
        },
        "bgm": {
            "file": bgm_info.get("file", ""),
            "license": bgm_info.get("license", ""),
        },
        "facts": facts_counts,
        "materials": materials_counts,
        "quality": quality_info if isinstance(quality_info, dict) else {},
        "overall_pass": overall_pass,
    }

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        logger.info("ステータスJSONを出力しました: %s", output_path)
    except OSError as e:
        logger.error("ステータスJSONの書き出しに失敗しました: %s", e)
        raise RuntimeError(f"ステータスJSONの書き出しに失敗しました: {e}")

    return status_data


def generate_credits(
    bgm_credits: list[str],
    source_credits: list[str],
    output_path: str,
) -> str:
    """統合クレジットファイルを生成する。

    Args:
        bgm_credits: BGM関連のクレジット行リスト。
        source_credits: 出典関連のクレジット行リスト。
        output_path: 出力ファイルのパス。

    Returns:
        生成されたクレジットテキスト。
    """
    lines: list[str] = []

    lines.append("=" * 40)
    lines.append("クレジット")
    lines.append("=" * 40)
    lines.append("")

    # 音声クレジット (常に含める)
    lines.append("【音声】")
    lines.append("・VOICEVOX (https://voicevox.hiroshiba.jp/)")
    lines.append("")

    # BGMクレジット
    if bgm_credits:
        lines.append("【BGM】")
        for credit in bgm_credits:
            lines.append(f"・{credit}")
        lines.append("")

    # 出典クレジット
    if source_credits:
        lines.append("【参考資料・出典】")
        for credit in source_credits:
            lines.append(f"・{credit}")
        lines.append("")

    lines.append("=" * 40)

    credits_text = "\n".join(lines)
    _write_text_file(output_path, credits_text)
    logger.info("クレジットを出力しました: %s", output_path)

    return credits_text


def _write_text_file(path: str, content: str) -> None:
    """テキストファイルを書き出すヘルパー。

    Args:
        path: 出力ファイルのパス。
        content: 書き出す内容。

    Raises:
        RuntimeError: ファイルの書き出しに失敗した場合。
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        out_path.write_text(content, encoding="utf-8")
    except OSError as e:
        logger.error("ファイルの書き出しに失敗しました: %s - %s", path, e)
        raise RuntimeError(f"ファイルの書き出しに失敗しました: {path} - {e}")


class ReportGenerator:
    """レポート生成を統合管理するクラス。

    全てのテキスト出力ファイルの生成を一括で行う。
    """

    def __init__(
        self,
        output_dir: str,
        status: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Args:
            output_dir: 出力ディレクトリのパス。
            status: パイプラインのステータス辞書。
        """
        self.output_dir = Path(output_dir)
        self.status = status or {}

    def generate_all_reports(
        self,
        output_dir: Optional[str] = None,
        status: Optional[dict[str, Any]] = None,
    ) -> dict[str, str]:
        """全てのレポートファイルを生成する。

        Args:
            output_dir: 出力ディレクトリ (省略時はコンストラクタの値)。
            status: ステータス辞書 (省略時はコンストラクタの値)。

        Returns:
            生成されたファイルパスの辞書 {"file_type": "path"}。
        """
        if output_dir:
            self.output_dir = Path(output_dir)
        if status:
            self.status = status

        self.output_dir.mkdir(parents=True, exist_ok=True)
        generated_files: dict[str, str] = {}

        topic = self.status.get("topic", "不明")
        mode = self.status.get("mode", "test")
        sources = self.status.get("sources", [])
        bgm_info = self.status.get("bgm", {})
        voicevox_info = self.status.get("voicevox", {})
        facts_info = self.status.get("facts", {})
        materials_info = self.status.get("materials", {})
        quality_info = self.status.get("quality", {})

        logger.info("レポート生成を開始します: %s", self.output_dir)

        # 1. ハッシュタグ生成
        try:
            hashtags_path = str(self.output_dir / "hashtags.txt")
            hashtags = generate_hashtags(topic, hashtags_path)
            generated_files["hashtags"] = hashtags_path
        except RuntimeError as e:
            logger.error("ハッシュタグの生成に失敗しました: %s", e)
            hashtags = list(BASE_HASHTAGS)

        # 2. クレジット生成
        try:
            bgm_credits: list[str] = []
            if bgm_info.get("file"):
                credit_line = bgm_info["file"]
                if bgm_info.get("license"):
                    credit_line += f" ({bgm_info['license']})"
                if bgm_info.get("author"):
                    credit_line += f" by {bgm_info['author']}"
                bgm_credits.append(credit_line)

            source_credits = [
                src.get("title", "") for src in sources if src.get("title")
            ]

            credits_path = str(self.output_dir / "credits.txt")
            generate_credits(bgm_credits, source_credits, credits_path)
            generated_files["credits"] = credits_path

            all_credits = bgm_credits + ["VOICEVOX (https://voicevox.hiroshiba.jp/)"]
        except RuntimeError as e:
            logger.error("クレジットの生成に失敗しました: %s", e)
            all_credits = []

        # 3. 概要欄テキスト生成
        try:
            description_path = str(self.output_dir / "description.txt")
            generate_description(
                topic, sources, all_credits, hashtags, description_path,
            )
            generated_files["description"] = description_path
        except RuntimeError as e:
            logger.error("概要欄テキストの生成に失敗しました: %s", e)

        # 4. 固定コメント生成
        try:
            comment_path = str(self.output_dir / "fixed_comment.txt")
            generate_fixed_comment(topic, sources, comment_path)
            generated_files["fixed_comment"] = comment_path
        except RuntimeError as e:
            logger.error("固定コメントの生成に失敗しました: %s", e)

        # 5. ステータスJSON生成
        try:
            status_path = str(self.output_dir / "status.json")
            generate_status_json(
                mode=mode,
                topic=topic,
                voicevox_info=voicevox_info,
                bgm_info=bgm_info,
                facts_info=facts_info,
                materials_info=materials_info,
                quality_info=quality_info,
                output_path=status_path,
            )
            generated_files["status"] = status_path
        except RuntimeError as e:
            logger.error("ステータスJSONの生成に失敗しました: %s", e)

        # 6. サマリー生成 (最後に生成 - 他の結果を含めるため)
        try:
            # ステータスを更新して品質情報を含める
            summary_status = dict(self.status)
            summary_status.setdefault("git_commit", get_git_commit())
            summary_status.setdefault("timestamp", datetime.now().isoformat())

            summary_path = str(self.output_dir / "summary.md")
            generate_summary(summary_status, summary_path)
            generated_files["summary"] = summary_path
        except RuntimeError as e:
            logger.error("サマリーの生成に失敗しました: %s", e)

        logger.info(
            "レポート生成が完了しました: %d件のファイルを生成",
            len(generated_files),
        )

        return generated_files
