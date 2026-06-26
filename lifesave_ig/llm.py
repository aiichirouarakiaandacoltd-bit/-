"""LLMプロバイダの抽象化。

MVPでは TemplateProvider（外部API不要）でテンプレ生成する。
将来 OpenAI などへ差し替えられるよう、共通インターフェースを定義する。
プロバイダは「投稿の構造化データ（dict）」を返す責務を持つ。
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class LLMProvider(ABC):
    """投稿生成プロバイダの共通インターフェース。"""

    name: str = "base"

    @abstractmethod
    def generate_post(self, theme: Dict[str, Any], fmt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """テーマ・フォーマット・商品コンテキストから投稿データを生成する。"""
        raise NotImplementedError


class TemplateProvider(LLMProvider):
    """テンプレートベースの生成器（既定・APIキー不要）。

    実際の文面組み立ては generator.TemplateBuilder に委譲する。
    ここでは「LLMを使わない実装」であることを表す薄いラッパに留め、
    将来のOpenAIProviderと同じI/Oで差し替えできるようにしている。
    """

    name = "template"

    def __init__(self, builder):
        self._builder = builder

    def generate_post(self, theme: Dict[str, Any], fmt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return self._builder.build(theme, fmt, context)


class OpenAIProvider(LLMProvider):
    """OpenAI API を使う生成器（雛形）。

    APIキーが無い、もしくはライブラリが無い場合は TemplateProvider に
    フォールバックする。プロンプト設計の骨子のみ実装し、実呼び出しは
    将来的に有効化できるようにしている（MVPでは安全側に倒す）。
    """

    name = "openai"

    def __init__(self, builder, model: str = "gpt-4o-mini", temperature: float = 0.7,
                 api_key_env: str = "OPENAI_API_KEY"):
        self._builder = builder
        self.model = model
        self.temperature = temperature
        self.api_key = os.environ.get(api_key_env, "")

    def _build_prompt(self, theme: Dict[str, Any], fmt: str, context: Dict[str, Any]) -> str:
        points = "\n".join(f"- {p}" for p in context.get("selling_points", []))
        policy = "\n".join(f"- {p}" for p in context.get("policy", []))
        return (
            f"あなたは{context.get('product')}のInstagram運用担当です。\n"
            f"商品: {context.get('product')}（{context.get('company')}）\n"
            f"訴求ポイント:\n{points}\n"
            f"必ず守るポリシー（薬機法・景表法）:\n{policy}\n"
            f"投稿テーマ: {theme.get('name')}\n"
            f"投稿フォーマット: {fmt}\n"
            "健康・治療・美容効果を断定せず、禁止表現を避けて生成してください。"
        )

    def generate_post(self, theme: Dict[str, Any], fmt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            # キーが無ければテンプレートで生成（テスト実行可能性を担保）
            return self._builder.build(theme, fmt, context)
        try:
            # 実APIを使う場合の差し込みポイント。
            # import openai 等はここで遅延importする想定。
            # prompt = self._build_prompt(theme, fmt, context)
            # ... API呼び出し → 構造化データへ変換 ...
            # 現状はMVPのためフォールバック。
            return self._builder.build(theme, fmt, context)
        except Exception:
            return self._builder.build(theme, fmt, context)


def build_provider(cfg: Dict[str, Any], builder) -> LLMProvider:
    """設定に応じてプロバイダを生成する。"""
    llm_cfg = cfg.get("llm", {})
    provider = (llm_cfg.get("provider") or "template").lower()
    if provider == "openai":
        return OpenAIProvider(
            builder,
            model=llm_cfg.get("model", "gpt-4o-mini"),
            temperature=llm_cfg.get("temperature", 0.7),
            api_key_env=llm_cfg.get("api_key_env", "OPENAI_API_KEY"),
        )
    return TemplateProvider(builder)
