"""
レポート生成モジュール (Report Generation Module)

昭和・平成動画自動制作システム用のレポート・メタデータ生成モジュール。
YouTube動画の説明文、ハッシュタグ、固定コメント、実行サマリー、
ステータスJSON、クレジットテキストを生成する。

チャンネル: 昭和・平成 なぜそうだったのか
"""

import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CHANNEL_NAME = "昭和・平成 なぜそうだったのか"
CHANNEL_TAGLINE = "昭和・平成の「当たり前」には、知られざる理由がありました。"

# 固定ハッシュタグ (全動画共通)
FIXED_HASHTAGS = [
    "#昭和",
    "#平成",
    "#なぜそうだったのか",
    "#昭和レトロ",
    "#懐かしい",
]

# トピック別追加ハッシュタグ
TOPIC_HASHTAG_MAP: Dict[str, List[str]] = {
    "テレビ": ["#ブラウン管テレビ", "#昭和のテレビ", "#テレビの歴史"],
    "電話": ["#黒電話", "#ダイヤル式電話", "#昭和の電話"],
    "布": ["#テレビカバー", "#レースの敷物", "#昭和の暮らし"],
    "食": ["#昭和の食卓", "#懐かしの味", "#昭和グルメ"],
    "学校": ["#昭和の学校", "#懐かしの学校", "#昭和の教育"],
    "給食": ["#学校給食", "#昭和の給食"],
    "遊び": ["#昭和の遊び", "#懐かしの遊び", "#昭和の子供"],
    "家電": ["#昭和の家電", "#三種の神器", "#レトロ家電"],
    "駄菓子": ["#駄菓子", "#駄菓子屋"],
    "銭湯": ["#銭湯", "#昭和の銭湯"],
    "鉄道": ["#鉄道", "#昭和の鉄道"],
    "車": ["#昭和の車", "#旧車"],
    "おもちゃ": ["#昭和のおもちゃ"],
    "住宅": ["#昭和の住宅", "#団地"],
    "商店街": ["#商店街", "#昭和の商店街"],
    "映画": ["#昭和の映画"],
    "音楽": ["#昭和の音楽", "#歌謡曲"],
    "ファッション": ["#昭和ファッション"],
    "結婚": ["#昭和の結婚"],
    "正月": ["#昭和の正月"],
    "夏休み": ["#昭和の夏休み"],
    "交通": ["#昭和の交通", "#懐かしの乗り物", "#昭和の街"],
    "文化": ["#昭和文化", "#昭和の暮らし", "#日本文化"],
}

# 偽URL検出パターン
_FAKE_URL_PATTERNS = [
    "example.com", "placeholder", "dummy", "test.com",
    "xxx", "yyy", "zzz", "hogehoge", "fugafuga",
]


# ===========================================================================
# ユーティリティ
# ===========================================================================

def _get_git_commit() -> str:
    """現在の git commit ハッシュ短縮形を返す。取得不能時は 'unknown'。"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return "unknown"


def _is_fake_url(url: str) -> bool:
    """URLがプレースホルダーや偽URLかどうかを判定する。"""
    if not url:
        return False
    lower = url.lower()
    return any(p in lower for p in _FAKE_URL_PATTERNS)


def _write_file(path: str, content: str) -> None:
    """テキストファイルを UTF-8 で書き出す。"""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ===========================================================================
# YouTube 説明文
# ===========================================================================

def generate_description(
    topic: str,
    sources: List[Dict[str, str]],
    credits: List[str],
    bgm_credits: List[str],
) -> str:
    """
    YouTube動画の説明文を生成する。

    実際に使用したソースURLのみを記載する。URLを捏造しない。
    偽URL (example.com, placeholder 等) は自動除外する。

    Args:
        topic: 動画トピック
        sources: 出典リスト。各項目は {"name": str, "url": str} 形式。
                 "title" キーも "name" として扱う。
                 url が空文字列または偽URLの場合は名前のみ表示。
        credits: 素材クレジット行のリスト (空リスト可)
        bgm_credits: BGMクレジット行のリスト (空リスト可)

    Returns:
        説明文テキスト
    """
    lines: List[str] = []

    # --- イントロ ---
    lines.append(f"【{topic}】")
    lines.append("")
    lines.append(CHANNEL_TAGLINE)
    lines.append(f"今回は「{topic}」について深掘りします。")
    lines.append("")

    # --- チャプター (タイムスタンプ用プレースホルダー) ---
    lines.append("▼ チャプター")
    lines.append("※ タイムスタンプは動画公開後に更新されます")
    lines.append("0:00 オープニング")
    lines.append("")

    # --- 出典 ---
    valid_sources = _filter_sources(sources)
    if valid_sources:
        lines.append("▼ 参考資料・出典")
        for src in valid_sources:
            name = src["name"]
            url = src.get("url", "").strip()
            if url and not _is_fake_url(url):
                lines.append(f"・{name}")
                lines.append(f"  {url}")
            else:
                lines.append(f"・{name}")
        lines.append("")

    # --- BGMクレジット ---
    actual_bgm = [c for c in bgm_credits if c and c.strip()]
    if actual_bgm:
        lines.append("▼ BGM")
        for credit in actual_bgm:
            lines.append(f"・{credit}")
        lines.append("")

    # --- 素材クレジット ---
    actual_credits = [c for c in credits if c and c.strip()]
    if actual_credits:
        lines.append("▼ 使用素材")
        for credit in actual_credits:
            lines.append(f"・{credit}")
        lines.append("")

    # --- 音声クレジット ---
    lines.append("▼ 音声")
    lines.append("・VOICEVOX (https://voicevox.hiroshiba.jp/)")
    lines.append("")

    # --- チャンネル情報 ---
    lines.append("▼ チャンネルについて")
    lines.append(
        f"「{CHANNEL_NAME}」では、昭和・平成時代の暮らしや文化について、"
        "「なぜそうだったのか」という視点から解説しています。"
    )
    lines.append("チャンネル登録・高評価よろしくお願いします！")
    lines.append("")

    # --- 注意書き ---
    lines.append("※ 本動画の内容は公開情報に基づくものであり、")
    lines.append("  一部の情報は地域や時代により異なる場合があります。")
    lines.append("※ 動画内の画像はイメージです。")
    lines.append("")

    # --- ハッシュタグ ---
    tags = generate_hashtags(topic)
    lines.append(" ".join(tags))

    return "\n".join(lines)


def _filter_sources(
    sources: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """有効な出典のみを返す。name/title キーいずれも受け付ける。"""
    result: List[Dict[str, str]] = []
    for src in sources:
        name = (src.get("name") or src.get("title", "")).strip()
        if not name:
            continue
        url = src.get("url", "").strip()
        if _is_fake_url(url):
            logger.warning("偽のURLを除外しました: %s", url)
            url = ""
        result.append({"name": name, "url": url})
    return result


# ===========================================================================
# ハッシュタグ
# ===========================================================================

def generate_hashtags(topic: str) -> List[str]:
    """
    動画用ハッシュタグを生成する。

    固定タグに加え、トピックから自動抽出したタグを追加する。

    Args:
        topic: 動画トピック

    Returns:
        ハッシュタグ文字列のリスト (各要素は # 付き)
    """
    tags = list(FIXED_HASHTAGS)

    # トピック固有タグ
    for keyword, keyword_tags in TOPIC_HASHTAG_MAP.items():
        if keyword in topic:
            for t in keyword_tags:
                if t not in tags:
                    tags.append(t)

    # トピック名そのものをタグ化 (30文字以下)
    topic_clean = topic.replace(" ", "").replace("　", "")
    if len(topic_clean) <= 28:
        topic_tag = f"#{topic_clean}"
        if topic_tag not in tags:
            tags.append(topic_tag)

    # 共通追加タグ
    for t in ["#日本の歴史", "#雑学", "#ゆっくり解説"]:
        if t not in tags:
            tags.append(t)

    return tags


# ===========================================================================
# 固定コメント
# ===========================================================================

def generate_fixed_comment(
    topic: str,
    shorts_info: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    動画の固定 (ピン留め) コメントを生成する。

    Args:
        topic: 動画トピック
        shorts_info: Shorts動画の情報リスト。
                     各項目は {"title": str, "url": str} 形式。
                     None または空リストの場合はShortsリンクプレースホルダー。

    Returns:
        固定コメント文テキスト
    """
    lines: List[str] = []

    lines.append("ご視聴ありがとうございます！")
    lines.append("")
    lines.append(f"「{topic}」、いかがでしたか？")
    lines.append("")

    # Shorts リンク
    if shorts_info:
        lines.append("この動画のショート版もあります：")
        for info in shorts_info:
            title = info.get("title", "Shorts")
            url = info.get("url", "")
            if url and not _is_fake_url(url):
                lines.append(f"  ▶ {title}: {url}")
            else:
                lines.append(f"  ▶ {title}: (公開後にリンクを追加します)")
        lines.append("")
    else:
        lines.append("ショート版は近日公開予定です。お楽しみに！")
        lines.append("")

    # 視聴者参加促進
    lines.append("あなたの思い出を教えてください！")
    lines.append(f"「{topic}」に関する思い出やエピソードがあれば、")
    lines.append("ぜひコメント欄で教えてください。")
    lines.append("皆さんの体験談をお待ちしています！")
    lines.append("")

    # チャンネル登録誘導
    lines.append("チャンネル登録＆通知ONで、最新動画をお見逃しなく！")
    lines.append("")

    # 出典注記
    lines.append("※この動画は公開資料・文献をもとに制作しています。")
    lines.append("※音声はVOICEVOXを使用しています。")
    lines.append("※内容に誤りや補足がございましたら、コメント欄でお知らせください。")

    return "\n".join(lines)


# ===========================================================================
# 実行サマリー (Markdown)
# ===========================================================================

def generate_summary(execution_data: Dict[str, Any]) -> str:
    """
    実行全体のMarkdownサマリーを生成する。

    Args:
        execution_data: 実行データ辞書。以下のキーを参照する:
            - project_name (str)
            - project_version (str)
            - mode (str): "test" / "production"
            - topic (str)
            - format_type (str): "long" / "shorts"
            - start_time (str, ISO format)
            - end_time (str, ISO format)
            - duration_seconds (float)
            - environment (dict): os, python_version, etc.
            - video (dict): duration, resolution, file_size, codec, etc.
            - research (dict): source_count, fact_count, verified_count, etc.
            - script (dict): char_count, chapter_count, estimated_duration
            - voicevox (dict): speaker_id, speed_scale, audio_duration
            - bgm (dict): file_name, source, license
            - materials (dict): total, ok, review, ng
            - quality (dict): checks_passed, checks_failed, overall_pass, results
            - git_commit (str)
            - output_dir (str)
            - errors (list of str)

    Returns:
        Markdown形式のサマリー文字列
    """
    lines: List[str] = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    topic = execution_data.get("topic", "不明")

    # --- ヘッダー ---
    lines.append(f"# 実行サマリー: {topic}")
    lines.append("")
    lines.append(f"生成日時: {now}")
    lines.append("")

    # --- プロジェクト情報 ---
    lines.append("## プロジェクト情報")
    lines.append("")
    lines.append(f"- プロジェクト: {execution_data.get('project_name', 'showa-heisei-video-automation')}")
    lines.append(f"- バージョン: {execution_data.get('project_version', '不明')}")
    lines.append(f"- モード: {execution_data.get('mode', '不明')}")
    lines.append(f"- Gitコミット: {execution_data.get('git_commit', _get_git_commit())}")
    lines.append(f"- 出力先: {execution_data.get('output_dir', '不明')}")
    lines.append("")

    # --- 環境情報 ---
    env = execution_data.get("environment", {})
    if env:
        lines.append("## 環境")
        lines.append("")
        for k, v in env.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    # --- 動画詳細 ---
    lines.append("## 動画詳細")
    lines.append("")
    lines.append(f"- トピック: {topic}")
    lines.append(f"- フォーマット: {execution_data.get('format_type', '不明')}")

    video = execution_data.get("video", {})
    if video:
        lines.append(f"- 動画尺: {video.get('duration', '不明')}")
        lines.append(f"- 解像度: {video.get('resolution', '不明')}")
        lines.append(f"- ファイルサイズ: {video.get('file_size', '不明')}")
        lines.append(f"- コーデック: {video.get('codec', '不明')}")
    lines.append("")

    # --- リサーチ ---
    research = execution_data.get("research", {})
    if research:
        lines.append("## リサーチ統計")
        lines.append("")
        lines.append(f"- ソース数: {research.get('source_count', 0)}")
        lines.append(f"- ファクト数: {research.get('fact_count', 0)}")
        if research.get("verified_count") is not None:
            lines.append(f"- 検証済み: {research['verified_count']}")
        if research.get("unverified_count") is not None:
            lines.append(f"- 未検証: {research['unverified_count']}")
        lines.append("")

    # --- スクリプト ---
    script = execution_data.get("script", {})
    if script:
        lines.append("## スクリプト")
        lines.append("")
        lines.append(f"- 文字数: {script.get('char_count', '不明')}")
        lines.append(f"- チャプター数: {script.get('chapter_count', '不明')}")
        if script.get("estimated_duration"):
            lines.append(f"- 推定尺: {script['estimated_duration']}")
        lines.append("")

    # --- 音声 ---
    vv = execution_data.get("voicevox", {})
    if vv:
        lines.append("## VOICEVOX音声")
        lines.append("")
        lines.append(f"- スピーカーID: {vv.get('speaker_id', vv.get('speaker', '不明'))}")
        lines.append(f"- 速度スケール: {vv.get('speed_scale', vv.get('speed', '不明'))}")
        lines.append(f"- 音声尺: {vv.get('audio_duration', '不明')}")
        lines.append("")

    # --- BGM ---
    bgm = execution_data.get("bgm", {})
    if bgm:
        lines.append("## BGM")
        lines.append("")
        lines.append(f"- ファイル: {bgm.get('file_name', bgm.get('file', '不明'))}")
        lines.append(f"- ソース: {bgm.get('source', '不明')}")
        lines.append(f"- ライセンス: {bgm.get('license', '不明')}")
        lines.append("")

    # --- 素材 ---
    mats = execution_data.get("materials", {})
    if mats:
        lines.append("## 素材")
        lines.append("")
        lines.append(f"- 総数: {mats.get('total', 0)}")
        lines.append(f"- OK: {mats.get('ok', 0)}")
        lines.append(f"- REVIEW: {mats.get('review', 0)}")
        lines.append(f"- NG: {mats.get('ng', 0)}")
        lines.append("")

    # --- 品質チェック ---
    quality = execution_data.get("quality", {})
    if quality:
        lines.append("## 品質チェック")
        lines.append("")
        overall = quality.get("overall_pass")
        if overall is True:
            lines.append("**結果: PASS**")
        elif overall is False:
            lines.append("**結果: FAIL**")
        else:
            lines.append("**結果: 未実行**")
        lines.append("")
        lines.append(f"- 合格: {quality.get('checks_passed', quality.get('passed_checks', 0))}")
        lines.append(f"- 不合格: {quality.get('checks_failed', 0)}")
        lines.append("")

        results = quality.get("results", [])
        if results:
            lines.append("| チェック項目 | 結果 | 詳細 |")
            lines.append("|---|---|---|")
            for r in results:
                name = r.get("check_name", "")
                passed = "PASS" if r.get("passed") else "FAIL"
                details = r.get("details", "").replace("|", "/")
                lines.append(f"| {name} | {passed} | {details} |")
            lines.append("")

    # --- 実行時間 ---
    lines.append("## 実行時間")
    lines.append("")
    lines.append(f"- 開始: {execution_data.get('start_time', execution_data.get('timestamp', '不明'))}")
    lines.append(f"- 終了: {execution_data.get('end_time', '不明')}")
    dur = execution_data.get("duration_seconds")
    if dur is not None:
        minutes = int(dur) // 60
        seconds = int(dur) % 60
        lines.append(f"- 所要時間: {minutes}分{seconds}秒 ({dur:.1f}秒)")
    lines.append("")

    # --- エラー ---
    errors = execution_data.get("errors", [])
    if errors:
        lines.append("## エラー")
        lines.append("")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("")

    # --- 最終判定 ---
    overall_pass = execution_data.get("overall_pass",
                                       quality.get("overall_pass", False) if quality else False)
    lines.append("## 最終判定")
    lines.append("")
    lines.append(f"**{'PASS - 公開可能' if overall_pass else 'FAIL - 要確認'}**")
    lines.append("")

    lines.append("---")
    lines.append(f"制作: {CHANNEL_NAME}")
    lines.append("")

    return "\n".join(lines)


# ===========================================================================
# ステータスJSON
# ===========================================================================

def generate_status_json(execution_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    実行ステータスの機械可読 JSON 辞書を生成する。

    Args:
        execution_data: 実行データ辞書 (generate_summary と同形式)

    Returns:
        ステータス辞書。キー: mode, topic, timestamp, git_commit,
        voicevox, bgm, research (fact_count, source_count),
        materials (total, ok, review, ng), quality_checks, overall_pass
    """
    now = datetime.now().isoformat()

    quality = execution_data.get("quality", {})
    materials = execution_data.get("materials", {})
    research = execution_data.get("research", {})
    voicevox = execution_data.get("voicevox", {})
    bgm = execution_data.get("bgm", {})

    status: Dict[str, Any] = {
        "generated_at": now,
        "mode": execution_data.get("mode", "unknown"),
        "topic": execution_data.get("topic", ""),
        "format_type": execution_data.get("format_type", "long"),
        "timestamp": {
            "start": execution_data.get("start_time", ""),
            "end": execution_data.get("end_time", ""),
            "duration_seconds": execution_data.get("duration_seconds"),
        },
        "git_commit": execution_data.get("git_commit", _get_git_commit()),
        "voicevox": {
            "speaker_id": voicevox.get("speaker_id", voicevox.get("speaker")),
            "speed_scale": voicevox.get("speed_scale", voicevox.get("speed")),
            "audio_duration": voicevox.get("audio_duration"),
        },
        "bgm": {
            "file_name": bgm.get("file_name", bgm.get("file", "")),
            "source": bgm.get("source", ""),
            "license": bgm.get("license", ""),
        },
        "research": {
            "fact_count": research.get("fact_count", 0),
            "source_count": research.get("source_count", 0),
        },
        "materials": {
            "total": materials.get("total", 0),
            "ok": materials.get("ok", 0),
            "review": materials.get("review", 0),
            "ng": materials.get("ng", 0),
        },
        "quality_checks": {
            "checks_passed": quality.get("checks_passed", quality.get("passed_checks", 0)),
            "checks_failed": quality.get("checks_failed", 0),
            "results": quality.get("results", []),
        },
        "overall_pass": quality.get("overall_pass", False),
        "errors": execution_data.get("errors", []),
    }

    return status


# ===========================================================================
# クレジット統合
# ===========================================================================

def generate_credits(
    materials: List[Dict[str, Any]],
    bgm_info: Optional[Dict[str, Any]] = None,
) -> str:
    """
    素材・BGMを統合したクレジットテキストを生成する。

    実際に使用されたもののみクレジットする。偽のクレジットは出力しない。

    Args:
        materials: 素材情報リスト (MaterialTracker の出力形式)。
                   rights_status が "OK" かつ credit_required が True のもののみ掲載。
        bgm_info: BGM情報辞書。キー: credit_text, source, source_url, file_name

    Returns:
        クレジットテキスト
    """
    lines: List[str] = []
    lines.append("=" * 50)
    lines.append("クレジット / Credits")
    lines.append("=" * 50)
    lines.append("")

    has_any = False

    # --- 音声クレジット (常に含める) ---
    lines.append("【音声】")
    lines.append("・VOICEVOX (https://voicevox.hiroshiba.jp/)")
    lines.append("")

    # --- 素材クレジット ---
    credit_materials = [
        m for m in materials
        if m.get("credit_required") and m.get("rights_status") == "OK"
    ]
    if credit_materials:
        has_any = True
        lines.append("【使用素材】")
        lines.append("")
        for m in credit_materials:
            ct = m.get("credit_text") or m.get("source_name", "")
            if ct:
                fname = os.path.basename(m.get("file_path", ""))
                lines.append(f"  {fname}")
                lines.append(f"    {ct}")
                url = (m.get("source_url") or "").strip()
                if url and not _is_fake_url(url):
                    lines.append(f"    {url}")
                lines.append("")

    # --- BGMクレジット ---
    if bgm_info:
        bgm_credit = (bgm_info.get("credit_text") or "").strip()
        if bgm_credit:
            has_any = True
            lines.append("【BGM】")
            lines.append("")
            lines.append(f"  {bgm_credit}")
            bgm_url = (bgm_info.get("source_url") or "").strip()
            if bgm_url and not _is_fake_url(bgm_url):
                lines.append(f"  {bgm_url}")
            lines.append("")

    if not has_any:
        lines.append("外部素材のクレジット表示は不要です。")
        lines.append("すべての素材は自動生成されたものです。")
        lines.append("")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("-" * 50)
    lines.append(f"生成日時: {now}")
    lines.append(f"制作: {CHANNEL_NAME}")
    lines.append("=" * 50)
    lines.append("")

    return "\n".join(lines)


# ===========================================================================
# 全レポート一括出力
# ===========================================================================

def generate_all_reports(
    output_dir: str,
    execution_data: Dict[str, Any],
) -> None:
    """
    全レポートファイルを出力する。

    出力ファイル:
        - description.txt: YouTube説明文
        - fixed_comment.txt: 固定コメント
        - hashtags.txt: ハッシュタグ
        - summary.md: 実行サマリー
        - status.json: ステータスJSON
        - credits.txt: クレジット

    Args:
        output_dir: 出力ディレクトリ
        execution_data: 実行データ辞書。generate_summary の execution_data に加え、
            以下のキーも参照する:
            - sources (list of dict): 出典情報 (name/title, url)
            - material_credits (list of str): 素材クレジット行
            - bgm_credits (list of str): BGMクレジット行
            - materials_list (list of dict): 素材情報リスト
            - bgm_info (dict): BGM情報
            - shorts_info (list of dict): Shorts情報 (title, url)
    """
    os.makedirs(output_dir, exist_ok=True)
    topic = execution_data.get("topic", "")

    logger.info("全レポート生成開始: output_dir=%s, topic='%s'", output_dir, topic)

    # --- description.txt ---
    sources = execution_data.get("sources", [])
    material_credits = execution_data.get("material_credits", [])
    bgm_credits_list = execution_data.get("bgm_credits", [])
    desc = generate_description(topic, sources, material_credits, bgm_credits_list)
    desc_path = os.path.join(output_dir, "description.txt")
    _write_file(desc_path, desc)
    logger.info("description.txt 保存: %s", desc_path)

    # --- fixed_comment.txt ---
    shorts_info = execution_data.get("shorts_info")
    comment = generate_fixed_comment(topic, shorts_info)
    comment_path = os.path.join(output_dir, "fixed_comment.txt")
    _write_file(comment_path, comment)
    logger.info("fixed_comment.txt 保存: %s", comment_path)

    # --- hashtags.txt ---
    tags = generate_hashtags(topic)
    tags_text = " ".join(tags) + "\n\n" + "\n".join(tags) + "\n"
    tags_path = os.path.join(output_dir, "hashtags.txt")
    _write_file(tags_path, tags_text)
    logger.info("hashtags.txt 保存: %s", tags_path)

    # --- summary.md ---
    summary = generate_summary(execution_data)
    summary_path = os.path.join(output_dir, "summary.md")
    _write_file(summary_path, summary)
    logger.info("summary.md 保存: %s", summary_path)

    # --- status.json ---
    status = generate_status_json(execution_data)
    status_path = os.path.join(output_dir, "status.json")
    _write_file(status_path, json.dumps(status, ensure_ascii=False, indent=2))
    logger.info("status.json 保存: %s", status_path)

    # --- credits.txt ---
    materials_list = execution_data.get("materials_list", [])
    bgm_info = execution_data.get("bgm_info")
    credits_text = generate_credits(materials_list, bgm_info)
    credits_path = os.path.join(output_dir, "credits.txt")
    _write_file(credits_path, credits_text)
    logger.info("credits.txt 保存: %s", credits_path)

    logger.info("全レポート生成完了: 6ファイル -> %s", output_dir)
