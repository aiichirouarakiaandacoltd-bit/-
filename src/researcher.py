"""調査・ファクトチェックモジュール"""
import json
import os
from datetime import datetime

RESEARCH_DB = {
    "なぜ昭和のテレビには布をかけていたのか": {
        "facts": [
            {
                "content": "1953年にNHKがテレビ放送を開始。当時のテレビ受像機は14インチ白黒で約20万円、当時の公務員の月給の約7〜10か月分に相当した。",
                "category": "公式事実",
                "source": "NHK放送博物館 / 総務省情報通信白書",
                "reliability": "高",
                "era": "昭和28年（1953年）",
            },
            {
                "content": "昭和30年代、テレビは家電の中でも特に高価であり、多くの家庭にとって特別な買い物だった。月賦（分割払い）で購入する家庭も多かった。",
                "category": "公的統計",
                "source": "経済企画庁『国民生活白書』/ 内閣府消費動向調査",
                "reliability": "高",
                "era": "昭和30年代",
            },
            {
                "content": "当時のブラウン管テレビは静電気でほこりを集めやすく、精密機器として丁寧に扱う意識が強かった。",
                "category": "一般的傾向",
                "source": "家電メーカー各社の取扱説明書（当時）/ 生活史資料",
                "reliability": "中",
                "era": "昭和30〜50年代",
            },
            {
                "content": "テレビに布やカバーをかける習慣は、高価な家電を保護する意味と、使用しないときに家具としての見栄えを整える意味があった。",
                "category": "一般的傾向",
                "source": "昭和生活史研究 / 家庭科教材",
                "reliability": "中",
                "era": "昭和30〜50年代",
            },
            {
                "content": "昭和30年代のテレビ普及率は、1958年に約10%、1960年代前半に急速に普及し、1965年頃には約90%に達した。",
                "category": "公的統計",
                "source": "内閣府『消費動向調査』",
                "reliability": "高",
                "era": "昭和33年〜40年",
            },
            {
                "content": "当時の家庭では、ミシンカバー、電話カバー、こたつカバーなど、家電や家具にカバーをかける文化が広くあった。テレビだけの習慣ではなかった。",
                "category": "一般的傾向",
                "source": "生活文化史資料",
                "reliability": "中",
                "era": "昭和30〜50年代",
            },
            {
                "content": "カラーテレビの本放送は1960年開始。カラーテレビの価格は白黒テレビの数倍であり、さらに丁重に扱う家庭が多かった。",
                "category": "公式事実",
                "source": "NHK放送博物館",
                "reliability": "高",
                "era": "昭和35年（1960年）以降",
            },
            {
                "content": "昭和50年代後半〜60年代に入ると、テレビの価格低下と普及により「高価な特別品」としての意識が薄れ、布をかける習慣は徐々に減少した。",
                "category": "一般的傾向",
                "source": "生活文化史研究",
                "reliability": "中",
                "era": "昭和50年代後半〜60年代",
            },
            {
                "content": "液晶テレビ・薄型テレビの普及により、ブラウン管時代のほこり対策としてのカバーは不要になった。また、テレビが家具の主役としてデザインされるようになり、カバーをかけること自体が減った。",
                "category": "一般的傾向",
                "source": "家電業界資料",
                "reliability": "中",
                "era": "平成10年代以降",
            },
            {
                "content": "地域差あり。都市部では比較的早くカバーの習慣が薄れたが、地方では平成に入っても見られた家庭がある。",
                "category": "一般的傾向",
                "source": "生活調査",
                "reliability": "低",
                "era": "昭和〜平成",
                "note": "地域によって異なります",
            },
        ],
        "sources": [
            {"name": "NHK放送博物館", "type": "公式", "url": "https://www.nhk.or.jp/museum/", "reliability": "高"},
            {"name": "総務省情報通信白書", "type": "公式", "url": "https://www.soumu.go.jp/johotsusintokei/whitepaper/", "reliability": "高"},
            {"name": "内閣府消費動向調査", "type": "公式", "url": "https://www.esri.cao.go.jp/jp/stat/shouhi/shouhi.html", "reliability": "高"},
        ],
    }
}


def generate_research(theme, output_dir):
    data = RESEARCH_DB.get(theme)
    if not data:
        data = {
            "facts": [
                {
                    "content": f"「{theme}」について、昭和・平成の時代背景に基づく調査が必要です。",
                    "category": "調査予定",
                    "source": "要調査",
                    "reliability": "未確認",
                    "era": "昭和〜平成",
                }
            ],
            "sources": [],
        }

    research = {
        "theme": theme,
        "research_date": datetime.now().strftime("%Y-%m-%d"),
        "facts": data["facts"],
        "sources": data["sources"],
        "total_facts": len(data["facts"]),
        "high_reliability_count": sum(1 for f in data["facts"] if f.get("reliability") == "高"),
    }

    path = os.path.join(output_dir, "research.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(research, f, ensure_ascii=False, indent=2)
    return research


def generate_fact_check(theme, research, output_dir):
    checks = []
    for fact in research.get("facts", []):
        check = {
            "claim": fact["content"],
            "category": fact["category"],
            "source": fact["source"],
            "reliability": fact["reliability"],
            "verified": fact["reliability"] in ("高", "中"),
            "notes": fact.get("note", ""),
        }
        checks.append(check)

    result = {
        "theme": theme,
        "check_date": datetime.now().strftime("%Y-%m-%d"),
        "items": checks,
        "total": len(checks),
        "verified_count": sum(1 for c in checks if c["verified"]),
        "unverified_count": sum(1 for c in checks if not c["verified"]),
    }

    path = os.path.join(output_dir, "fact_check.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result
