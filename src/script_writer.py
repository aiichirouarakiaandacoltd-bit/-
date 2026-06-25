"""台本生成モジュール"""
import json
import os

SCRIPT_TEMPLATES = {
    "なぜ昭和のテレビには布をかけていたのか": {
        "long": {
            "narration": [
                "昭和の家庭では、テレビに布をかける光景が珍しくありませんでした。",
                "なぜ高価な家電を、わざわざ毎日覆っていたのでしょうか。",
                "今回は、テレビに布をかけていた本当の理由と、その背景にある昭和の暮らしをお伝えします。",
                "",
                "昭和28年、1953年。NHKがテレビ放送を開始しました。",
                "当時のテレビ受像機は、14インチの白黒テレビで、価格はおよそ20万円。",
                "これは当時の公務員の月給の、7か月分から10か月分に相当しました。",
                "つまり、テレビは家庭にとって、ちょっとした買い物ではなかったのです。",
                "",
                "昭和30年代、テレビの普及が始まりました。",
                "1958年、昭和33年の時点で、テレビの普及率はおよそ10パーセント。",
                "しかし、その後の数年で急速に広がり、1965年、昭和40年頃には約90パーセントに達しました。",
                "多くの家庭が、月賦、今で言う分割払いでテレビを購入していました。",
                "",
                "では、なぜ布をかけていたのでしょうか。",
                "理由は、大きく分けて3つあります。",
                "",
                "1つ目は、ほこり対策です。",
                "当時のブラウン管テレビは、静電気を帯びやすく、ほこりを集めやすい構造でした。",
                "精密機器であるテレビを、ほこりから守るためにカバーをかけていたのです。",
                "",
                "2つ目は、高価な家電の保護です。",
                "先ほどお伝えしたように、テレビは月給の何か月分もする高額商品でした。",
                "大切な家電を傷や汚れから守りたいという気持ちは、自然なことでした。",
                "",
                "3つ目は、家具としての見栄えです。",
                "当時の家庭では、テレビに限らず、ミシンや電話にもカバーをかける文化がありました。",
                "使わないときには布をかけて、部屋の見た目を整える習慣があったのです。",
                "",
                "昭和35年、1960年にはカラーテレビの放送が始まりました。",
                "カラーテレビの価格は白黒テレビの数倍。",
                "さらに丁重に扱う家庭が増え、布をかける習慣はますます定着しました。",
                "",
                "しかし、昭和50年代後半から60年代に入ると、状況が変わり始めます。",
                "テレビの価格が下がり、一家に複数台のテレビがある家庭も増えました。",
                "「テレビは特別な品物」という意識が薄れていったのです。",
                "",
                "そして、平成に入り、液晶テレビや薄型テレビが普及すると、",
                "ブラウン管時代のほこり対策としてのカバーは不要になりました。",
                "テレビ自体がインテリアの一部としてデザインされるようになり、",
                "布をかけること自体が、見かけなくなっていきました。",
                "",
                "ただし、地域によっては、平成に入ってもテレビに布をかけている家庭はありました。",
                "この習慣が消えた時期は、全国一律ではありません。",
                "",
                "テレビに布をかけていたのは、単なる昭和の風習ではありませんでした。",
                "高価な家電を大切にし、部屋の見た目も気にかける。",
                "当時の暮らしの中で、布をかけることには合理的な理由があったのです。",
                "",
                "技術が進み、テレビの価格が下がり、形が変わったことで、",
                "この習慣は自然と消えていきました。",
                "もし皆さまのご家庭にもテレビカバーがあったなら、",
                "それは、当時の生活と価値観をよく映しているのかもしれません。",
            ],
            "sections": [
                {"title": "冒頭", "start_line": 0, "end_line": 2, "visual": "昭和の茶の間イメージ、テレビにカバーがかかった光景"},
                {"title": "導入", "start_line": 3, "end_line": 3, "visual": "今回のテーマタイトル表示"},
                {"title": "テレビ放送開始", "start_line": 4, "end_line": 8, "visual": "昭和28年の年代表示、当時のテレビのイメージ、価格比較図"},
                {"title": "普及の歩み", "start_line": 9, "end_line": 13, "visual": "普及率グラフ、月賦のイメージ"},
                {"title": "理由の提示", "start_line": 14, "end_line": 15, "visual": "3つの理由リスト"},
                {"title": "理由1：ほこり対策", "start_line": 16, "end_line": 18, "visual": "ブラウン管テレビのイメージ、ほこりの説明図"},
                {"title": "理由2：保護", "start_line": 19, "end_line": 21, "visual": "高価な家電を大切にする家庭のイメージ"},
                {"title": "理由3：見栄え", "start_line": 22, "end_line": 25, "visual": "ミシンカバー、電話カバーなど当時の生活イメージ"},
                {"title": "カラーテレビ", "start_line": 26, "end_line": 29, "visual": "カラーテレビ登場のイメージ、昭和35年の年代表示"},
                {"title": "変化の始まり", "start_line": 30, "end_line": 33, "visual": "昭和50〜60年代の茶の間イメージ"},
                {"title": "消えた理由", "start_line": 34, "end_line": 38, "visual": "液晶テレビのイメージ、現代のリビング"},
                {"title": "地域差", "start_line": 39, "end_line": 40, "visual": "日本地図イメージ"},
                {"title": "まとめ", "start_line": 41, "end_line": 48, "visual": "昭和の茶の間と現代のリビングの比較"},
            ],
        },
        "shorts": [
            {
                "id": "short_01",
                "title": "なぜ昭和のテレビには布をかけていた？",
                "narration": [
                    "なぜ昭和のテレビには布をかけていたのか。",
                    "当時テレビは月給7か月分もする高額品でした。",
                    "ほこり対策と部屋の見栄えを整えるためにカバーをかけていたのです。",
                    "テレビが安くなり液晶に変わったことでこの習慣は消えました。",
                ],
            },
            {
                "id": "short_02",
                "title": "昭和のテレビは月給何か月分？",
                "narration": [
                    "昭和28年のテレビの値段はおよそ20万円。",
                    "月給の7か月分もする高額商品でした。",
                    "だからこそ布をかけ大切に使っていたのです。",
                    "7年で普及率10パーセントから90パーセントに広がりました。",
                ],
            },
        ],
    }
}


def generate_long_script(theme, output_dir):
    template = SCRIPT_TEMPLATES.get(theme, {}).get("long")
    if not template:
        template = _generate_generic_long_script(theme)

    narration_text = "\n".join(template["narration"])
    script_path = os.path.join(output_dir, "script_long.txt")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(narration_text)

    narration_path = os.path.join(output_dir, "narration_long.txt")
    narration_lines = [line for line in template["narration"] if line.strip()]
    with open(narration_path, "w", encoding="utf-8") as f:
        f.write("\n".join(narration_lines))

    editing_plan = {
        "theme": theme,
        "format": "long",
        "sections": template.get("sections", []),
        "total_lines": len(template["narration"]),
    }
    plan_path = os.path.join(output_dir, "editing_plan.json")
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(editing_plan, f, ensure_ascii=False, indent=2)

    return template


def generate_shorts_scripts(theme, count, output_dir):
    shorts = SCRIPT_TEMPLATES.get(theme, {}).get("shorts", [])
    if not shorts:
        shorts = [_generate_generic_short(theme, i) for i in range(count)]

    results = []
    for i, short in enumerate(shorts[:count]):
        narration_text = "\n".join(short["narration"])
        idx = f"{i+1:02d}"
        script_path = os.path.join(output_dir, f"script_short_{idx}.txt")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(narration_text)

        narration_path = os.path.join(output_dir, f"narration_short_{idx}.txt")
        narration_lines = [line for line in short["narration"] if line.strip()]
        with open(narration_path, "w", encoding="utf-8") as f:
            f.write("\n".join(narration_lines))

        results.append(short)
    return results


def _generate_generic_long_script(theme):
    return {
        "narration": [
            f"{theme}。",
            "今回はこの疑問について、時代背景から解説します。",
            "",
            "この習慣が広まったのには、当時の社会や技術が深く関わっています。",
            "当時の暮らしの中では、これは合理的な選択でした。",
            "",
            "時代が進み、技術や社会が変わったことで、",
            "この習慣は自然と姿を消していきました。",
            "当時を知る方にとっては、懐かしい記憶かもしれません。",
        ],
        "sections": [
            {"title": "冒頭", "start_line": 0, "end_line": 2, "visual": "テーマに関連するイメージ"},
            {"title": "本編", "start_line": 3, "end_line": 5, "visual": "解説図"},
            {"title": "まとめ", "start_line": 6, "end_line": 8, "visual": "比較図"},
        ],
    }


def _generate_generic_short(theme, index):
    return {
        "id": f"short_{index+1:02d}",
        "title": theme[:20],
        "narration": [
            f"{theme}",
            "当時の暮らしでは、これには合理的な理由がありました。",
            "時代が変わり、今では見かけなくなりました。",
            "詳しくは長尺動画で解説しています。",
        ],
    }
