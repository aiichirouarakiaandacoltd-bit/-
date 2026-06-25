"""
動画制作パッケージ出力モジュール Ver1.0
videos/NNN_slug/ 配下の12フォルダ構造とMarkdownファイルを生成する
"""

import re
from datetime import datetime
from pathlib import Path

SYSTEM_VERSION = "Ver1.0"

# 話速から1分あたりの文字数を概算（VOICEVOX 青山龍星 基準）
_CHARS_PER_MIN_BASE = 330  # speed=1.0 のとき約330字/分


def _estimate_duration_sec(narration_text: str, speed: float = 0.87) -> float:
    chars = len(re.sub(r"\s", "", narration_text))
    return (chars / (_CHARS_PER_MIN_BASE * speed)) * 60


def _fmt_sec(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m}分{s:02d}秒"


def _slug(theme: str) -> str:
    """テーマ文字列を安全なフォルダ名スラグに変換する"""
    import hashlib
    safe = re.sub(r"[^\w぀-ヿ一-鿿]", "_", theme)
    safe = re.sub(r"_+", "_", safe).strip("_")[:24]
    h = hashlib.md5(theme.encode()).hexdigest()[:4]
    return f"{safe}_{h}" if safe else h


def next_video_number(base_dir: Path) -> int:
    """videos/ 配下の NNN_* を走査して次の番号を返す"""
    existing = []
    if base_dir.exists():
        for d in base_dir.iterdir():
            if d.is_dir():
                m = re.match(r"^(\d{3})", d.name)
                if m:
                    existing.append(int(m.group(1)))
    return max(existing, default=0) + 1


def make_video_dir(base_dir: Path, theme: str) -> Path:
    """連番付きの動画出力ルートディレクトリを作成して返す"""
    num = next_video_number(base_dir)
    slug = _slug(theme)
    root = base_dir / f"{num:03d}_{slug}"
    for sub in [
        "01_research", "02_titles", "03_thumbnail", "04_script",
        "05_voice", "06_subtitles", "07_bgm", "08_ai_image_prompts",
        "09_description", "10_rights_check", "11_video", "12_upload_package",
    ]:
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


# ─────────────────────────────────────────────────────────────────────────────

def _dry_run_header() -> list[str]:
    return ["> ⚠️ **DRY-RUN モード**: 音声生成・動画レンダリングはスキップされています。", ""]


def write_research_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "01_research" / "research.md"
    title = script.get("title", "")
    subtitle = script.get("subtitle", "")
    chapters = script.get("chapters", {})

    lines = ["# リサーチメモ", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        f"**タイトル**: {title}",
        f"**サブタイトル**: {subtitle}",
        "",
        "## 各章のポイント",
        "",
    ]
    for i, (ch, data) in enumerate(chapters.items(), 1):
        narr = data.get("narration", "")
        preview = narr[:200].replace("\n", " ") + ("…" if len(narr) > 200 else "")
        lines += [
            f"### 第{i}章: {ch}｜{data.get('headline', '')}",
            preview, "",
        ]
    lines += [
        "## 参考にすべき公式情報",
        "（荒木さんが確認後に追記してください）", "",
        "## 未確認事項・要確認",
        "（荒木さんが確認後に追記してください）", "",
        "> ⚠️ 台本の事実確認は荒木さんが必ず実施してください。AIは誤情報を含む場合があります。",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_titles_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "02_titles" / "titles.md"
    base_title = script.get("title", "テーマ")
    subtitle = script.get("subtitle", "")
    core = re.sub(r"｜.*", "", base_title).strip()

    ideas = [
        (f"なぜ昭和の日本人は{core}したのか？理由を知って驚く人続出",
         "「なぜ」という問いが知的好奇心を刺激する", "昭和経験者55歳以上", "〇〇を具体的に書き換えてください"),
        (f"{core}【昭和の常識】",
         "「常識」が共感と驚きを呼ぶ", "昭和経験者とその子世代", "短くシンプルで視認性が高い"),
        (f"【昭和】{core}の本当の理由",
         "「本当の理由」が秘密感を演出", "歴史・教養好きな中高年", "サムネと組み合わせると効果的"),
        (f"昭和の日本人が{core}をやっていた驚きの理由",
         "「驚きの理由」がクリックを促す", "幅広い年齢層", "「驚き」が強すぎないよう注意"),
        (f"{core}｜令和の今では考えられない昭和の文化",
         "令和との対比が共感と懐かしさを生む", "55歳以上・子育て世代", "令和比較がある動画に適している"),
        (f"あの頃は当たり前だった｜{core}の時代背景",
         "「あの頃」が回想欲求を刺激", "65歳以上女性視聴者", "「当たり前」が共感を呼ぶ"),
        (f"【令和人には伝わらない】昭和の{core}とは何だったのか",
         "令和人への対比が世代共感を生む", "昭和経験者", "やや排他的なので使用には注意"),
        (f"知らなかった！{core}の歴史と理由を解説",
         "「知らなかった」が自己発見欲求を刺激", "教養動画好き", "タイトルにびっくりマークを多用しすぎない"),
        (f"昭和と平成を生きた人だけが分かる｜{core}の物語",
         "「自分だけが分かる」という特別感", "55歳以上", "「物語」が感情に訴える"),
        (f"懐かしい！{core}｜あなたはいくつ覚えていますか？",
         "チェックリスト的な問いがコメント誘発", "昭和懐かし系全般", "コメント欄が活発になりやすい"),
    ]

    lines = ["# タイトル案一覧", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        f"**元タイトル**: {base_title}",
        f"**サブタイトル**: {subtitle}", "",
        "> 荒木さんが最終タイトルを選択・修正してください。", "",
    ]
    for i, (title, click, audience, note) in enumerate(ideas, 1):
        lines += [
            f"## 案{i}",
            f"**タイトル**: {title}",
            f"- クリック理由: {click}",
            f"- 想定視聴者: {audience}",
            f"- 注意点: {note}", "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_thumbnail_ideas_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "03_thumbnail" / "thumbnail_ideas.md"
    title = script.get("title", "")
    core = re.sub(r"｜.*", "", title).strip()[:16]

    ideas = [
        (f"なぜ？\n{core}", "左に大きな問いかけテキスト、右に昭和情景（イメージ素材）",
         "昭和の風景・生活シーン", "セピア〜ブラウン系グラデーション", "「なぜ？」を大きく配置してクリック率を高める"),
        ("あの頃\nみんなやってた", "中央にメインテキスト、下にサブテキスト",
         "家族や職場の昭和シーン（イメージ素材）", "温かみのあるオレンジ〜アンバー系", "「みんな」という共感ワードが効果的"),
        ("昭和の常識\n令和ではありえない", "上段に「昭和の常識」、昭和と令和の対比ビジュアル",
         "昭和と令和の対比イメージ", "左半分セピア・右半分モダンブルー", "対比レイアウトは視覚的インパクトが高い"),
        (f"知ってた？\n{core}の理由", "問いかけテキストを強調、背景に昭和素材",
         "昭和の日常生活シーン（イメージ素材）", "深みのある藍色〜紺", "「知ってた？」が自然なクリックを誘発"),
        (f"懐かしい…\n{core}", "感情的な言葉を大きく、懐かし写真風加工",
         "昭和の家庭や職場（イメージ素材）", "ノスタルジックなセピア系", "65歳以上女性視聴者に特に響きやすい"),
    ]

    lines = ["# サムネイル案一覧", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        f"**動画タイトル**: {title}", "",
        "> ⚠️ 実在人物の顔・表情・服装をAIで生成・改変しないでください。",
        "> イメージ素材は動画内で「再現イメージ」と明記してください。", "",
    ]
    for i, (text, layout, subject, bg, note) in enumerate(ideas, 1):
        lines += [
            f"## 案{i}",
            f"**文言**: `{text}`",
            f"- 画面構成: {layout}",
            f"- メイン素材: {subject}",
            f"- 背景案: {bg}",
            f"- 注意点: {note}", "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_script_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "04_script" / "script.md"
    title = script.get("title", "")
    subtitle = script.get("subtitle", "")
    chapters = script.get("chapters", {})
    all_narr = "".join(d.get("narration", "") for d in chapters.values())
    total_chars = len(all_narr)
    est_sec = _estimate_duration_sec(all_narr)

    lines = ["# 台本", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        f"**タイトル**: {title}",
        f"**サブタイトル**: {subtitle}",
        f"**推定尺**: {_fmt_sec(est_sec)}（VOICEVOX話速0.87基準）",
        f"**総文字数**: {total_chars}字", "",
        "> ⚠️ この台本はAIが生成しました。事実確認・固有名詞の確認を必ず行ってください。", "",
        "---", "",
    ]
    for i, (ch_name, ch_data) in enumerate(chapters.items(), 1):
        headline = ch_data.get("headline", ch_name)
        narration = ch_data.get("narration", "（ナレーション未生成）")
        ch_sec = _estimate_duration_sec(narration)
        lines += [
            f"## 第{i}章: {ch_name}｜{headline}",
            f"*推定: {_fmt_sec(ch_sec)} / {len(narration)}字*", "",
            narration, "",
            "---", "",
        ]
    lines += [
        "## エンディング", "",
        "チャンネル登録・高評価をよろしくお願いします。",
        "コメントであなたの思い出を教えてください。", "",
        "---", "",
        "## 確認チェックリスト（荒木さんへ）", "",
        "- [ ] 全章のナレーションを通読済み",
        "- [ ] 固有名詞・企業名・人名の確認済み",
        "- [ ] 数字・年号・統計の確認済み",
        "- [ ] 「とされています」等の断定回避表現を使用済み確認",
        "- [ ] 特定個人・企業への誹謗中傷がないこと確認済み",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_voice_check_md(
    root: Path, voicevox_ok: bool, speed: float,
    audio_durations: dict, dry_run: bool = False,
) -> Path:
    path = root / "05_voice" / "voice_check.md"
    total_sec = sum(audio_durations.values()) if audio_durations else 0

    if dry_run:
        conn = "未接続（dry-run のためスキップ）"
        wav = "未生成（dry-run）"
    else:
        conn = "接続OK ✅" if voicevox_ok else "接続失敗 ❌"
        wav = "narration.wav（生成済み）✅" if voicevox_ok else "生成失敗 ❌"

    lines = [
        "# 音声チェック", "",
        f"- VOICEVOX接続状態: {conn}",
        f"- 話者: 青山龍星",
        f"- speaker ID: 13",
        f"- 話速: {speed}",
        f"- 音声ファイル: {wav}",
        f"- 推定音声時間: {_fmt_sec(total_sec)}", "",
        "## 章別音声時間", "",
    ]
    if audio_durations:
        for ch, sec in audio_durations.items():
            lines.append(f"- {ch}: {_fmt_sec(sec)}")
    else:
        lines.append("（未生成）")

    lines += [
        "",
        "## 確認チェックリスト（荒木さんへ）", "",
        "- [ ] VOICEVOXの読み間違いがないこと確認",
        "- [ ] 固有名詞・人名の読みが正確なこと確認",
        "- [ ] 話速が適切であること確認（速すぎ・遅すぎでないか）",
        "- [ ] 章の区切りが自然であること確認",
        "- [ ] 全体の音声を通して聴いた", "",
        "## 注意点",
        "（荒木さんが気になった箇所を記入してください）",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_bgm_check_md(
    root: Path, bgm_path: str, bgm_exists: bool, dry_run: bool = False,
) -> Path:
    path = root / "07_bgm" / "bgm_check.md"
    lines = [
        "# BGMチェック", "",
        f"- BGMファイル名: UNL1337.wav",
        f"- BGMファイルパス: {bgm_path}",
        f"- ファイル存在確認: {'OK ✅' if bgm_exists else '見つかりません ❌'}",
        f"- 音量設定: -28.0 dB",
        f"- フェードイン: 2秒",
        f"- フェードアウト: 3秒",
        f"- 説明欄表記: 楽曲提供：箕輪レコーズ", "",
        "## 確認チェックリスト（荒木さんへ）", "",
        "- [ ] BGMがナレーションに対して適切な音量か確認",
        "- [ ] フェードイン・フェードアウトが自然か確認",
        "- [ ] BGMの雰囲気がテーマに合っているか確認",
        "- [ ] 説明欄に「楽曲提供：箕輪レコーズ」を記載済みか確認", "",
        "## 注意点",
        "- BGM提供: 箕輪レコーズ",
        "- 使用許可: 本チャンネル専用ライセンス（他チャンネルへの転用禁止）",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_ai_image_prompts_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "08_ai_image_prompts" / "prompts.md"
    chapters = script.get("chapters", {})
    image_descriptions = script.get("image_descriptions", {})

    lines = ["# AI画像生成プロンプト", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        "> ⚠️ **重要な制限事項**",
        "> - 実在人物の顔・表情・服装をAIで生成・改変しないでください",
        "> - 著名人・政治家の顔をAIで生成しないでください",
        "> - 出典不明画像の使用を前提にしないでください",
        "> - 「再現イメージ」と明記が必要な素材には必ずテロップを入れてください", "",
    ]
    for i, (ch_name, ch_data) in enumerate(chapters.items(), 1):
        headline = ch_data.get("headline", ch_name)
        descs = image_descriptions.get(ch_name, [f"{ch_name}の昭和イメージ"])
        lines += [
            f"## 第{i}章: {ch_name}｜{headline}", "",
            "| # | 用途 | プロンプト（日本語） | 注意 |",
            "|---|------|---------------------|------|",
        ]
        for j, desc in enumerate(descs, 1):
            lines.append(f"| {j} | 章{i}-シーン{j} | {desc} | 再現イメージと明記 |")
        if descs:
            lines += [
                "",
                f"**英語プロンプト例**（シーン1）:",
                "```",
                f"Showa era Japan, {descs[0]}, nostalgic atmosphere, warm sepia lighting, "
                f"no real human faces, cinematic composition, 16:9",
                "```",
            ]
        lines.append("")

    lines += [
        "## 使用不可素材",
        "- 実在人物の写真・映像（権利許諾なしのもの）",
        "- テレビ放送・CM・映画の映像・画像",
        "- 著作権が不明な昭和時代の写真",
        "- SNS・個人ブログに掲載されている写真", "",
        "## 利用可能な素材",
        "- AI生成画像（「再現イメージ」テロップ必須）",
        "- 本システムが生成したスライド画像",
        "- 荒木さんが権利確認済みのパブリックドメイン素材",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_description_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "09_description" / "description.md"
    title = script.get("title", "")
    subtitle = script.get("subtitle", "")
    chapters = script.get("chapters", {})
    timecodes = {"共感": "0:00", "発見": "1:30", "考察": "4:30", "令和比較": "8:00", "余韻": "10:30"}

    body = [
        subtitle, "",
        "━" * 20,
        "【この動画で分かること】",
        "━" * 20,
    ]
    for ch_name, ch_data in chapters.items():
        body.append(f"✔ {ch_data.get('headline', ch_name)}")
    body += [
        "",
        "━" * 20,
        "【目次】",
        "━" * 20,
    ]
    for i, (ch_name, ch_data) in enumerate(chapters.items()):
        tc = timecodes.get(ch_name, f"{i*2}:00")
        body.append(f"{tc} 第{i+1}章：{ch_name}｜{ch_data.get('headline', '')}")
    body += [
        "",
        "━" * 20,
        "【参考情報】",
        "※ 荒木さんが確認済みの参考URLをここに追記してください",
        "━" * 20, "",
        "━" * 20,
        "【クレジット】",
        "━" * 20,
        "音声：VOICEVOX 青山龍星",
        "楽曲提供：箕輪レコーズ", "",
        "━" * 20,
        "【免責事項】",
        "━" * 20,
        "本動画は昭和・平成の時代背景を教養目的で解説するものです。",
        "内容は一般的な調査・研究に基づいており、特定の個人・企業を",
        "誹謗中傷する意図はありません。",
        "事実関係については最新情報を各自でご確認ください。", "",
        "#昭和 #平成 #なぜそうだったのか #昭和平成 #日本文化 #教養 #懐かしい",
    ]

    lines = ["# YouTube説明文", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        "> コピーしてYouTubeの説明欄に貼り付けてください。",
        "> 参考URLは荒木さんが追記してください。", "",
        "---", "```",
    ] + body + ["```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_fixed_comment_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "09_description" / "fixed_comment.md"
    title = script.get("title", "この動画")
    core = re.sub(r"｜.*", "", title).strip()

    body = [
        "【あなたの記憶を教えてください】", "",
        f"「{core}」を見て、",
        "あなたのご家庭ではどうでしたか？", "",
        "💬 当時の思い出",
        "💬 今との違いを感じること",
        "💬 子供や孫に伝えたいこと", "",
        "ぜひコメントで教えてください。",
        "皆さんの体験談をお聞きするのが楽しみです。", "",
        "━" * 20,
        "▶ 関連動画もあわせてどうぞ",
        "（投稿後に荒木さんが関連動画URLを追記してください）",
        "━" * 20,
    ]

    lines = ["# 固定コメント", ""]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        "> コピーしてYouTubeの固定コメントに投稿してください。", "",
        "---", "```",
    ] + body + ["```", "",
        "## 注意点",
        "- 過度な煽りや感情的な表現は避けています",
        "- 関連動画URLは投稿後に追記してください",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_rights_check_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "10_rights_check" / "rights_check.md"
    title = script.get("title", "")

    lines = [
        "# 権利チェック", "",
        f"**タイトル**: {title}",
        f"**確認日**: （荒木さんが記入してください）", "",
        "## 使用素材", "",
        "- 画像: AI生成スライド画像（「再現イメージ」テロップ表示済み）",
        "- 動画: AI生成スライドのみ（実写映像なし）",
        "- BGM: UNL1337.wav（箕輪レコーズ・本チャンネル使用許可済み）",
        "- ナレーション: VOICEVOX 青山龍星（AI合成音声）",
        "- 参考URL: （荒木さんが調査した参考URLをここに記入してください）", "",
        "## 注意事項", "",
        "- 出典不明素材: 使用していません（AI生成画像のみ）",
        "- 人物画像: 実在人物の実写画像は使用していません",
        "- AI生成画像: スライド画像はすべて「再現イメージ」として生成済み",
        "- 商用利用確認: BGM（箕輪レコーズ）✅ / VOICEVOX（商用利用可）✅",
        "- YouTube説明欄に必要な表記:",
        "  ```",
        "  音声：VOICEVOX 青山龍星",
        "  楽曲提供：箕輪レコーズ",
        "  ```", "",
        "## 判定", "",
        "- 投稿可能: ✅（以下の確認チェックリストをすべて完了した場合）",
        "- 要確認: 参考URLの記載 / 台本中の固有名詞・統計の出典",
        "- 使用不可: 実在人物の実写写真・映像 / 権利不明のBGM・画像", "",
        "## 確認チェックリスト（荒木さんへ）", "",
        "- [ ] AI生成画像には「再現イメージ」テロップを表示済み",
        "- [ ] 実在人物の実写写真・映像を使用していない",
        "- [ ] テレビ映像・CM・映画の映像を使用していない",
        "- [ ] BGMはUNL1337.wav（箕輪レコーズ）のみ使用",
        "- [ ] 説明欄に「音声：VOICEVOX 青山龍星」を記載済み",
        "- [ ] 説明欄に「楽曲提供：箕輪レコーズ」を記載済み",
        "- [ ] 断定を避ける表現（〜とされています等）を使用",
        "- [ ] 特定企業・個人の誹謗中傷なし",
        "- [ ] 参考URLを保存・記録済み",
        "- [ ] 荒木による台本内容確認完了", "",
        "> ⚠️ 自動投稿禁止。荒木さんが手動で確認・投稿すること。",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_video_check_md(
    root: Path, video_exists: bool, bgm_path: str, bgm_exists: bool,
    has_narration: bool, error_reason: str = "", dry_run: bool = False,
) -> Path:
    path = root / "11_video" / "video_check.md"

    if dry_run:
        gen_status = "スキップ（dry-run モード）"
        mp4_status = "未生成（dry-run）"
        next_action = "dry-runを確認後、本番実行: python create_video.py --theme \"テーマ名\""
    elif video_exists:
        gen_status = "成功 ✅"
        mp4_status = "output.mp4（生成済み）✅"
        next_action = "動画を再生して最初から最後まで視聴してください"
    else:
        gen_status = "失敗 ❌"
        mp4_status = "未生成"
        next_action = error_reason or "エラーログを確認してください"

    lines = [
        "# 動画生成チェック", "",
        f"- 動画生成: {gen_status}",
        f"- output.mp4: {mp4_status}",
        f"- 使用音声: {'narration.wav（VOICEVOX 青山龍星）' if has_narration and not dry_run else '未生成（dry-run）' if dry_run else '未生成'}",
        f"- 使用BGM: {'UNL1337.wav（箕輪レコーズ）✅' if bgm_exists else '未配置 ❌'}",
        f"- 使用字幕: {'subtitles.srt（生成済み）' if not dry_run else '未生成（dry-run）'}",
        f"- 使用画像: AI生成スライド画像（1920×1080 PNG）",
        f"- 生成できなかった場合の理由: {error_reason or 'なし'}",
        f"- 荒木が次にやること: {next_action}", "",
        "## 確認チェックリスト（荒木さんへ）", "",
        "- [ ] 動画を最初から最後まで視聴した",
        "- [ ] 映像とナレーションが同期している",
        "- [ ] 字幕の誤字脱字がない",
        "- [ ] BGM音量がナレーションに対して適切",
        "- [ ] フェードイン・フェードアウトが自然",
        "- [ ] 画質・解像度に問題がない",
        "- [ ] エンディングが自然に終わっている", "",
        "## 注意点",
        "（荒木さんが気になる点を記入してください）",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_upload_checklist_md(script: dict, root: Path, dry_run: bool = False) -> Path:
    path = root / "12_upload_package" / "upload_checklist.md"
    title = script.get("title", "")

    lines = [
        "# 投稿前チェックリスト", "",
        f"**タイトル**: {title}", "",
        "> ⚠️ このシステムは自動投稿しません。投稿は必ず荒木さんが手動で行ってください。", "",
    ]
    if dry_run:
        lines += _dry_run_header()
    lines += [
        "## タイトル", "",
        "- [ ] タイトルを1本選んだ",
        "- [ ] 誇張しすぎていない",
        "- [ ] 視聴者がクリックする理由がある", "",
        "## サムネイル", "",
        "- [ ] 文字が読みやすい",
        "- [ ] 人物や対象が大きい",
        "- [ ] 内容とズレていない", "",
        "## 台本", "",
        "- [ ] 数字・日付・固有名詞を確認した",
        "- [ ] 読み間違いしやすい語を確認した",
        "- [ ] 冒頭で視聴理由が明確",
        "- [ ] 最後まで見る理由がある", "",
        "## 音声", "",
        "- [ ] 青山龍星で出力されている",
        "- [ ] 話速が適切",
        "- [ ] 読み間違いがない",
        "- [ ] 音量が適切", "",
        "## BGM", "",
        "- [ ] BGMが小さすぎない／大きすぎない",
        "- [ ] ナレーションを邪魔していない",
        "- [ ] 説明欄に「楽曲提供：箕輪レコーズ」と記載した", "",
        "## 権利", "",
        "- [ ] 出典不明素材を使っていない",
        "- [ ] AI生成人物画像を使っていない",
        "- [ ] 参考URLを保存した",
        "- [ ] 説明欄に必要表記を入れた", "",
        "## 最終確認", "",
        "- [ ] 動画を最初から最後まで確認した",
        "- [ ] 字幕を確認した",
        "- [ ] 説明文を確認した",
        "- [ ] 固定コメントを確認した",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_summary_md(
    root: Path, theme: str, script: dict, speed: float,
    bgm_path: str, bgm_exists: bool, audio_durations: dict,
    voicevox_ok: bool, video_exists: bool, file_map: dict,
    dry_run: bool = False,
) -> Path:
    path = root / "summary.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    chapters = script.get("chapters", {})
    total_sec = sum(audio_durations.values()) if audio_durations else sum(
        _estimate_duration_sec(d.get("narration", "")) for d in chapters.values()
    )

    def fstatus(p) -> str:
        if p is None:
            return "未生成"
        fp = Path(p)
        if fp.exists():
            kb = fp.stat().st_size // 1024
            sz = f"({kb}KB)" if kb > 0 else "(<1KB)"
            try:
                rel = fp.relative_to(root)
            except ValueError:
                rel = fp
            return f"✅ {rel} {sz}"
        return "❌ 未生成"

    lines = [
        "# 動画生成サマリー",
        f"**システムバージョン**: YouTube動画自動生成システム {SYSTEM_VERSION}",
        "",
    ]
    if dry_run:
        lines += ["> ⚠️ **DRY-RUN モード**: 音声生成・動画レンダリングはスキップされています。", ""]
    lines += [
        "## 1. 基本情報", "",
        f"- テーマ：{theme}",
        f"- 生成日時：{now}",
        f"- 推定動画尺：{_fmt_sec(total_sec)}",
        f"- VOICEVOX話者：青山龍星（speaker ID: 13）",
        f"- VOICEVOX話速：{speed}",
        f"- BGM：{'UNL1337.wav（箕輪レコーズ）✅' if bgm_exists else '未配置 ⚠️'}",
        f"- 出力フォルダ：{root}",
        f"- DRY-RUNモード：{'はい（音声・動画は未生成）' if dry_run else 'いいえ（本番実行）'}",
        "",
        "## 2. 生成ファイル一覧", "",
        f"- リサーチ：{fstatus(file_map.get('research'))}",
        f"- タイトル案：{fstatus(file_map.get('titles'))}",
        f"- サムネイル案：{fstatus(file_map.get('thumbnail_ideas'))}",
        f"- 台本：{fstatus(file_map.get('script'))}",
        f"- 音声：{fstatus(file_map.get('narration'))}",
        f"- 音声チェック：{fstatus(file_map.get('voice_check'))}",
        f"- 字幕：{fstatus(file_map.get('subtitle'))}",
        f"- BGMチェック：{fstatus(file_map.get('bgm_check'))}",
        f"- 画像プロンプト：{fstatus(file_map.get('prompts'))}",
        f"- 説明文：{fstatus(file_map.get('description'))}",
        f"- 固定コメント：{fstatus(file_map.get('fixed_comment'))}",
        f"- 権利チェック：{fstatus(file_map.get('rights_check'))}",
        f"- 動画ファイル：{fstatus(file_map.get('video'))}",
        f"- 動画チェック：{fstatus(file_map.get('video_check'))}",
        f"- 投稿チェックリスト：{fstatus(file_map.get('upload_checklist'))}",
        "",
        "## 3. 投稿前チェック", "",
        "- [ ] 台本の事実確認",
        "- [ ] 数字・固有名詞・日付の確認",
        "- [ ] VOICEVOXの読み間違い確認",
        "- [ ] 字幕の誤字脱字確認",
        "- [ ] BGM音量確認",
        "- [ ] 素材の権利確認",
        "- [ ] YouTube説明欄の表記確認",
        "- [ ] 固定コメント確認",
        "- [ ] 動画を最初から最後まで視聴確認",
        "",
        "## 4. 注意点", "",
        "- 未確認情報：台本の固有名詞・数字・統計は荒木さんが確認してください",
        "- 権利注意：AI生成画像には「再現イメージ」テロップ必須、実在人物の顔生成禁止",
        "- 音声注意：VOICEVOX読み間違いを必ず確認してください",
        "- 投稿前に荒木さんが確認すべきこと：動画通し視聴・権利チェック・説明文の参考URL追記",
        "",
        "> ⚠️ **このシステムは自動投稿しません。投稿は必ず荒木さんが手動で行ってください。**",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path
