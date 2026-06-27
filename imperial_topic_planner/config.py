"""企画作成システム設定."""

CHANNEL_NAME = "日本が誇る皇室物語"
CHANNEL_PROMISE = "公式事実で、静かな感動を。"
TARGET_AUDIENCE = "55歳以上、特に65歳以上の女性、スマートフォン視聴中心"

SCORING_WEIGHTS = {
    "viewer_fit": 20,
    "official_facts": 20,
    "emotion": 15,
    "rights_safety": 15,
    "long_video": 10,
    "shorts": 10,
    "outsource": 10,
}

PASS_THRESHOLD = 70
PRIORITY_THRESHOLD = 80

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
    "execution.log",
]
