"""企画作成システム設定."""

CHANNEL_NAME = "日本が誇る皇室物語"
CHANNEL_PROMISE = "公式事実で、静かな感動を。"
TARGET_AUDIENCE = "55歳以上、特に65歳以上の女性、スマートフォン視聴中心"

# --- 新スコアリング（10軸・各10点満点＝合計100点） ---
SCORING_AXES = {
    "demand":             {"label": "需要スコア",               "max": 10},
    "competitor_growth":  {"label": "競合伸長スコア",           "max": 10},
    "reproducibility":    {"label": "少登録者でも伸びる再現性", "max": 10},
    "channel_fit":        {"label": "皇室チャンネル適合性",     "max": 10},
    "official_evidence":  {"label": "公式根拠の有無",           "max": 10},
    "rights_safety":      {"label": "権利リスク",               "max": 10},
    "senior_fit":         {"label": "65歳以上女性への適合性",   "max": 10},
    "long_video":         {"label": "長尺化可否",               "max": 10},
    "shorts_potential":   {"label": "Shorts展開可否",           "max": 10},
    "production_cost":    {"label": "推定制作コスト",           "max": 10},
}

PASS_THRESHOLD = 60
PRIORITY_THRESHOLD = 75
HOLD_THRESHOLD = 50

PROHIBITED_EXPRESSIONS = [
    "衝撃", "激震", "涙が止まらない", "世界が絶賛", "神対応",
    "隠された真実", "誰も知らない", "暴露", "日本中が涙",
    "世界が震えた", "全米が泣いた", "前代未聞", "歴史的快挙",
    "大スクープ", "独占入手", "関係者激白", "極秘情報",
    "禁断の真実", "闇に葬られた", "確執", "断絶", "怒り",
    "衝撃の真実", "驚愕の事実", "ヤバすぎる", "緊急速報",
    "マスコミが隠す", "まさかの展開", "炎上", "崩壊", "秘密",
    "涙", "メディアが隠した",
]

RECOMMENDED_EXPRESSIONS = [
    "静かに語られる", "心に残る", "温かな交流", "受け継がれる思い",
    "公式記録に残る", "忘れられない一場面", "日本らしい気品", "年月を越えて",
]

PRIORITY_SOURCES = [
    "宮内庁公式サイト",
    "宮内庁公式YouTube",
    "宮内庁公式Instagram",
    "外務省・自治体・博物館・美術館・大学など公的機関",
    "王室・大使館・公的団体の公式発表",
    "NHK・日テレ・朝日・読売・毎日・産経・共同通信など信頼できる報道",
]

RISK_CATEGORIES = [
    "事実誤認リスク",
    "権利リスク",
    "収益化リスク",
    "炎上リスク",
    "高齢視聴者との不一致",
    "外注者の作業負担",
    "素材調達難易度",
]

OUTPUT_FILES = [
    "01_topic_candidates.md",
    "02_selected_topics.md",
    "03_rejected_topics.md",
    "04_fact_source_plan.md",
    "05_long_video_plan.md",
    "06_shorts_plan.md",
    "07_title_thumbnail_plan.md",
    "08_risk_check_report.md",
    "09_package_summary.md",
    "topic_plan.json",
    "execution.log",
]

# YouTube指標の重み（需要スコア算出用）
YOUTUBE_METRIC_WEIGHTS = {
    "views": 0.15,
    "ctr": 0.25,
    "avg_watch_time_pct": 0.25,
    "repeat_viewers_pct": 0.15,
    "shorts_to_long_rate": 0.20,
}
