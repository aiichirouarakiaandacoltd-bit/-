"""ライフセーブ21プラス Instagram投稿生成・予約管理システム。

将来的なWeb管理画面化を見据え、ロジックはこのパッケージに集約し、
CLI（main.py）は薄いインターフェースとして実装している。
"""

__version__ = "0.1.0"

PRODUCT_NAME = "ライフセーブ21プラス"
COMPANY_NAME = "株式会社ナチュラルウィル"

# 投稿ステータス（人間確認フロー）
STATUSES = ["draft", "review", "approved", "scheduled", "posted", "rejected"]

# 対応する投稿フォーマット
FORMATS = ["feed", "carousel", "reel", "story"]
