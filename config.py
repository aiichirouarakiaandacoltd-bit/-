from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_PACKAGES_DIR = OUTPUT_DIR / "packages"
OUTPUT_LATEST_DIR = OUTPUT_DIR / "latest"
LOGS_DIR = PROJECT_ROOT / "logs"
INPUT_DIR = PROJECT_ROOT / "input"

CHANNEL_NAME = "日本が誇る皇室物語"
CHANNEL_PROMISE = "公式事実で、静かな感動を。"
TARGET_AUDIENCE = "55歳以上、特に65歳以上の女性、日本国内、スマートフォン視聴中心"

VIDEO_SPECS = {
    "long": {
        "width": 1920,
        "height": 1080,
        "fps": 30,
        "duration_min_seconds": 8 * 60,
        "duration_max_seconds": 12 * 60,
    },
    "shorts": {
        "width": 1080,
        "height": 1920,
        "fps": 30,
        "duration_min_seconds": 45.0,
        "duration_max_seconds": 59.5,
    },
}

BGM_SETTINGS = {
    "file_name": "UNL1337.wav",
    "provider": "箕輪レコーズ",
    "credit_text": "楽曲提供：箕輪レコーズ",
}

BGM_CONFIG_PATH = PROJECT_ROOT / "bgm_config.json"

VOICEVOX_SETTINGS = {
    "speaker_name": "青山龍星",
    "speed": 0.88,
}

PROHIBITED_IMAGE_TYPES = [
    "ai_generated_royal_face",
    "face_composite",
    "expression_modified",
    "clothing_modified",
    "age_modified",
    "unverified_press_photo",
    "フェイク画像",
    "無断使用の私的写真",
]

PROHIBITED_EXPRESSIONS = [
    "世界が絶賛",
    "神対応",
    "衝撃",
    "激震",
    "日本中が涙",
    "隠された真実",
    "秘密の友情",
    "世界が平伏",
    "メディアが隠した",
    "本物の友情",
    "家族のように迎えた",
    "プロトコルを無視",
    "涙が止まらない",
    "親友",
    "確執",
    "断絶",
    "怒り",
    "暴露",
    "衝撃の真実",
    "驚愕の事実",
    "ヤバすぎる",
    "緊急速報",
    "マスコミが隠す",
    "まさかの展開",
    "炎上",
    "崩壊",
    "秘密",
]

NG_INNER_FEELINGS = [
    "胸を痛めた",
    "涙をこらえた",
    "心から願っていた",
    "決意した",
    "深く感動した",
    "悲しみに暮れた",
    "内心激怒",
    "密かに喜んでいた",
    "本心は",
    "心の中で",
    "実は～を望んでいる",
]

OFFICIAL_SOURCES = [
    "宮内庁",
    "首相官邸",
    "外務省",
    "NHK",
    "共同通信",
    "時事通信",
    "主要全国紙（読売・朝日・毎日・産経・日経）",
]


class FactStatus:
    CONFIRMED = "confirmed"
    PARTIAL = "partial"
    UNCONFIRMED = "unconfirmed"
    REJECTED = "rejected"


class RightsStatus:
    OK = "ok"
    REVIEW = "review"
    NG = "ng"


class Priority:
    NOW = "今すぐ制作"
    THIS_WEEK = "今週中に制作"
    EVERGREEN = "長期常緑企画"
    SEASONAL = "季節・記念日連動"
    ON_HOLD = "保留・様子見"
