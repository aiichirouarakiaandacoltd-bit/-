"""メタデータ生成モジュール（タイトル・概要欄・ハッシュタグ・固定コメント・サムネイル文言）"""
import os
import json
import csv
import logging

logger = logging.getLogger(__name__)

TITLE_TEMPLATES = [
    "なぜ{subject}だったのか ― 昭和の暮らしに隠された理由",
    "{subject}の本当の理由 ― 昭和・平成の生活を振り返る",
    "今では消えた「{subject}」、なぜ当時は必要だった？",
    "昭和の家庭では当たり前だった{subject}、その背景とは",
]


def generate_titles(theme, output_dir):
    subject = theme.replace("なぜ", "").replace("のか", "").replace("昭和の", "")
    titles = [t.format(subject=subject) for t in TITLE_TEMPLATES]
    titles.insert(0, theme)

    path = os.path.join(output_dir, "title_candidates.txt")
    with open(path, "w", encoding="utf-8") as f:
        for i, title in enumerate(titles):
            f.write(f"案{i+1}: {title}\n")
    return titles


def generate_description(theme, sources, output_dir):
    lines = [
        f"【{theme}】",
        "",
        "昭和・平成の暮らしの中で当たり前だったことについて、",
        "「なぜ当時はそうだったのか」を、時代背景や社会の仕組みから解説しています。",
        "",
        "━━━━━━━━━━━━━━━━━",
        "📌 目次",
        "0:00 はじめに",
        "0:30 当時の光景",
        "2:00 なぜそうだったのか",
        "5:00 時代背景",
        "7:00 なぜ消えたのか",
        "8:30 まとめ",
        "━━━━━━━━━━━━━━━━━",
        "",
        "📚 参考資料",
    ]
    for src in sources[:5]:
        lines.append(f"・{src.get('name', '不明')} ({src.get('url', '')})")
    lines.extend([
        "",
        "🎵 使用BGM",
        "・システム生成アンビエントBGM（商用利用可）",
        "",
        "📝 注記",
        "・本動画では、当時の生活風景を説明するため、一部に再現イメージを使用しています。",
        "・本チャンネルは非公式の解説チャンネルです。",
        "・動画内の情報は調査に基づいていますが、地域や時代により異なる場合があります。",
        "",
        "📧 お問い合わせ",
        "・概要欄のメールアドレスまでお願いいたします。",
        "",
    ])

    path = os.path.join(output_dir, "description.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return lines


def generate_hashtags(theme, category, output_dir):
    base_tags = [
        "#昭和", "#平成", "#なぜそうだったのか", "#昭和の暮らし",
        "#懐かしい", "#昭和レトロ", "#生活史", "#日本の歴史",
        "#昭和時代", "#平成時代", "#暮らしの歴史",
    ]
    category_tags = {
        "暮らし": ["#昭和の家庭", "#昭和家電", "#生活文化"],
        "学校": ["#昭和の学校", "#給食", "#学校生活"],
        "仕事": ["#昭和の会社", "#仕事文化", "#終身雇用"],
        "交通": ["#昭和の交通", "#鉄道", "#昭和の電車"],
        "通信・メディア": ["#テレビ", "#昭和のテレビ", "#メディア史"],
        "買い物・商売": ["#商店街", "#デパート", "#昭和の買い物"],
        "食文化": ["#昭和の食", "#食文化", "#懐かしの味"],
        "娯楽": ["#昭和の娯楽", "#エンタメ史"],
        "社会・制度": ["#社会制度", "#昭和の制度"],
    }
    tags = base_tags + category_tags.get(category, [])

    path = os.path.join(output_dir, "hashtags.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(" ".join(tags[:15]))
    return tags


def generate_pinned_comment(theme, output_dir):
    comments = [
        f"ご視聴ありがとうございます。",
        f"皆さまのご家庭にも、テレビに布をかけていた思い出はありますか？",
        f"当時の暮らしの中で印象に残っていることがあれば、ぜひコメントでお聞かせください。",
        f"地域によって違いがあった方も、ぜひ教えてください。",
        f"次に取り上げてほしい昭和・平成の習慣がありましたら、お気軽にどうぞ。",
    ]

    path = os.path.join(output_dir, "pinned_comment.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(comments))
    return comments


def generate_thumbnail_text(theme, output_dir):
    texts = [
        "なぜ布をかけた？",
        "昭和のテレビ事情",
        "月給7か月分！",
        "なぜ消えた？",
    ]

    path = os.path.join(output_dir, "thumbnail_text.txt")
    with open(path, "w", encoding="utf-8") as f:
        for t in texts:
            f.write(f"・{t}\n")
    return texts


def generate_source_list(images_info, output_dir):
    path = os.path.join(output_dir, "source_list.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ファイル名", "種別", "出典", "使用箇所", "AI生成"])
        for img in images_info:
            writer.writerow([
                os.path.basename(img["path"]),
                img.get("type", "画像"),
                "システム生成",
                img.get("section", ""),
                "はい",
            ])
        writer.writerow(["bgm.wav", "BGM", "システム生成アンビエント", "全編", "はい"])

    return path


def generate_rights_check(images_info, output_dir):
    path = os.path.join(output_dir, "rights_check.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ファイル名", "権利状態", "クレジット要否", "備考"])
        for img in images_info:
            writer.writerow([
                os.path.basename(img["path"]),
                "OK",
                "不要",
                "システム生成イメージ",
            ])
        writer.writerow(["bgm.wav", "OK", "不要", "システム生成BGM"])
        writer.writerow(["音声", "OK", "不要", "TTS生成"])

    return path
