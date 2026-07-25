"""日本が誇る皇室物語 制作支援システム / 機械処理モジュール群.

このパッケージが担当するのは機械処理のみである。
    フォルダ生成／テンプレート出力／CSV整形／禁止表現の機械検出／
    必須項目の欠落検出／ID採番／再実行時の履歴退避／承認内容の反映／
    最終フォルダ生成／実行ログ記録

調査・事実判定・台本執筆・企画評価・監査は行わない（サブエージェントの担当）。
外部APIを呼ばない。
"""

__all__ = [
    "logger",
    "input_parser",
    "scaffold",
    "id_assigner",
    "forbidden_checker",
    "required_checker",
    "duplication_checker",
    "approval_builder",
    "package_builder",
]
