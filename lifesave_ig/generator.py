"""投稿案の生成。

TemplateBuilder が各フォーマット（feed / carousel / reel / story）の
構造化データを組み立てる。PostGenerator はテーマ解決・LLMプロバイダ選択・
リスクチェックを束ねる上位ロジック。
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

from . import config
from .llm import build_provider
from .risk import RiskChecker

FORMATS = ["feed", "carousel", "reel", "story"]


def _slug(text: str) -> str:
    h = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return h


class TemplateBuilder:
    """テンプレートから投稿の各要素を生成する（APIキー不要）。"""

    def __init__(self, recommended: Dict[str, Any]):
        self.rec = recommended

    # ---- 共通パーツ -------------------------------------------------
    def _hashtags(self, theme: Dict[str, Any], max_count: int) -> List[str]:
        tags = list(self.rec.get("hashtags", {}).get("core", []))
        tags += self.rec.get("hashtags", {}).get("theme", [])
        # テーマ固有キーワードをタグ化
        for kw in theme.get("keywords", []):
            tag = "#" + str(kw).replace(" ", "").replace("・", "")
            if tag not in tags:
                tags.append(tag)
        tags += self.rec.get("hashtags", {}).get("lifestyle", [])
        # 重複除去（順序維持）
        seen, out = set(), []
        for t in tags:
            if t not in seen:
                seen.add(t)
                out.append(t)
        return out[:max_count]

    def _cta(self, theme: Dict[str, Any]) -> str:
        ctas = self.rec.get("cta", [])
        if theme.get("id") == "free-consult":
            return ctas[0] if ctas else "詳しくはDMでご相談ください"
        # テーマIDのハッシュで安定的に選ぶ（毎回同じ結果＝テストしやすい）
        if not ctas:
            return "詳しくはDMでご相談ください"
        idx = int(_slug(theme.get("id", "")), 16) % len(ctas)
        return ctas[idx]

    def _hook(self, theme: Dict[str, Any]) -> str:
        hooks = self.rec.get("hooks", [])
        if not hooks:
            return theme.get("name", "")
        idx = int(_slug(theme.get("id", "x")), 16) % len(hooks)
        return hooks[idx]

    # ---- フォーマット別 --------------------------------------------
    def _caption(self, theme: Dict[str, Any], ctx: Dict[str, Any], cta: str) -> str:
        product = ctx.get("product", "ライフセーブ21プラス")
        lines = [
            f"【{theme.get('name')}】",
            "",
            theme.get("summary", ""),
            "",
            f"・{theme.get('pain', '')}",
            f"・{theme.get('background', '')}",
            "",
            f"キッチン、洗面、浴室、シャワー、洗濯まで。",
            f"毎日使う水だからこそ、住まい全体で整えるという考え方です。",
            "",
            f"オール浄水・オールナノバブル水の{product}。",
            "浄水＋ナノバブル水という選択を、暮らしに。",
            "",
            cta,
        ]
        return "\n".join(lines)

    def _feed(self, theme: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "title": f"{theme.get('name')}",
            "image_text": self._hook(theme),
        }

    def _carousel(self, theme: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        product = ctx.get("product", "ライフセーブ21プラス")
        slides = [
            {"no": 1, "role": "タイトル", "image_text": self._hook(theme),
             "note": "興味を引く一言。続きが気になる構成に。"},
            {"no": 2, "role": "悩み", "image_text": theme.get("pain", ""),
             "note": "読者の「あるある」に共感する。"},
            {"no": 3, "role": "原因・背景", "image_text": theme.get("background", ""),
             "note": "なぜそれが起きるのかを丁寧に。断定はしない。"},
            {"no": 4, "role": "提案", "image_text": f"{product}という選択\nオール浄水＋オールナノバブル水",
             "note": "家中の水を見直す、というソリューションを提示。"},
            {"no": 5, "role": "暮らしの変化イメージ",
             "image_text": "キッチン・洗面・浴室・シャワー・洗濯まで\n住まい全体で水を整える毎日へ",
             "note": "効果の断定はせず、暮らしのイメージで伝える。"},
            {"no": 6, "role": "よくある不安",
             "image_text": "工事や費用が気になる…\nまずはご相談だけでも大丈夫です",
             "note": "心理的ハードルを下げる。"},
            {"no": 7, "role": "DM・資料請求への誘導",
             "image_text": self._cta(theme),
             "note": "明確なCTA。保存・DMを促す。"},
        ]
        return {
            "title": f"{theme.get('name')}（カルーセル）",
            "image_text": self._hook(theme),
            "slides": slides,
        }

    def _reel(self, theme: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        product = ctx.get("product", "ライフセーブ21プラス")
        hook = self._hook(theme)
        script = {
            "duration_sec": "30〜45秒",
            "hook_3s": hook,
            "scenes": [
                {"time": "0-3秒", "on_screen": hook,
                 "narration": f"{hook}", "note": "最初の3秒で離脱を防ぐ"},
                {"time": "3-10秒", "on_screen": theme.get("pain", ""),
                 "narration": f"{theme.get('pain', '')}", "note": "悩みに共感"},
                {"time": "10-20秒", "on_screen": theme.get("background", ""),
                 "narration": f"{theme.get('background', '')}", "note": "背景をやさしく説明"},
                {"time": "20-35秒",
                 "on_screen": "オール浄水＋オールナノバブル水\n家中の水を見直す",
                 "narration": f"キッチンも、お風呂も、シャワーも。{product}なら住まい全体の水を整えられます。",
                 "note": "提案。効果は断定しない"},
                {"time": "35-45秒", "on_screen": self._cta(theme),
                 "narration": self._cta(theme), "note": "CTA。DM・保存を促す"},
            ],
        }
        return {
            "title": f"{theme.get('name')}（リール台本）",
            "image_text": hook,
            "reel": script,
        }

    def _story(self, theme: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
        frames = [
            {"no": 1, "image_text": self._hook(theme), "interaction": "「気になる」スタンプ"},
            {"no": 2, "image_text": theme.get("summary", ""), "interaction": "アンケート: 浄水器ある？/ない"},
            {"no": 3, "image_text": "家中の水を見直すという選択", "interaction": "質問BOX"},
            {"no": 4, "image_text": self._cta(theme), "interaction": "DMリンク / 上スワイプ"},
        ]
        return {
            "title": f"{theme.get('name')}（ストーリーズ）",
            "image_text": self._hook(theme),
            "story": {"frames": frames},
        }

    def build(self, theme: Dict[str, Any], fmt: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        fmt = (fmt or "feed").lower()
        if fmt not in FORMATS:
            raise ValueError(f"未対応のフォーマット: {fmt}（対応: {', '.join(FORMATS)}）")

        builders = {
            "feed": self._feed,
            "carousel": self._carousel,
            "reel": self._reel,
            "story": self._story,
        }
        body = builders[fmt](theme, ctx)
        cta = self._cta(theme)
        post: Dict[str, Any] = {
            "theme_id": theme.get("id"),
            "theme": theme.get("name"),
            "format": fmt,
            "title": body.get("title"),
            "image_text": body.get("image_text"),
            "caption": self._caption(theme, ctx, cta),
            "hashtags": self._hashtags(theme, ctx.get("max_hashtags", 15)),
            "cta": cta,
        }
        for extra in ("slides", "reel", "story"):
            if extra in body:
                post[extra] = body[extra]
        return post


class PostGenerator:
    """テーマ解決〜生成〜リスクチェックまでを束ねる上位クラス。"""

    def __init__(self, cfg: Optional[Dict[str, Any]] = None):
        self.cfg = cfg or config.load_config()
        self.themes_data = config.load_json(self.cfg["data"]["themes"])
        self.recommended = config.load_json(self.cfg["data"]["recommended"])
        self.builder = TemplateBuilder(self.recommended)
        self.provider = build_provider(self.cfg, self.builder)
        self.checker = RiskChecker(self.cfg)

    # ---- テーマ -----------------------------------------------------
    @property
    def themes(self) -> List[Dict[str, Any]]:
        return self.themes_data.get("themes", [])

    def find_theme(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        key = (name_or_id or "").strip()
        for t in self.themes:
            if t.get("id") == key or t.get("name") == key:
                return t
        # 部分一致も許容
        for t in self.themes:
            if key and key in t.get("name", ""):
                return t
        return None

    def _context(self) -> Dict[str, Any]:
        product = self.cfg["product"]
        return {
            "product": product.get("name"),
            "company": product.get("company"),
            "selling_points": product.get("selling_points", []),
            "policy": product.get("policy", []),
            "max_hashtags": self.cfg.get("hashtags", {}).get("max_count", 15),
        }

    # ---- 生成 -------------------------------------------------------
    def generate(self, theme_name: str, fmt: str) -> Dict[str, Any]:
        theme = self.find_theme(theme_name)
        if theme is None:
            available = "、".join(t["name"] for t in self.themes)
            raise ValueError(f"テーマが見つかりません: '{theme_name}'\n登録テーマ: {available}")
        ctx = self._context()
        post = self.provider.generate_post(theme, fmt, ctx)
        post["id"] = f"{theme['id']}-{fmt}-{_slug(theme['id'] + fmt)}"
        post["status"] = self.cfg.get("calendar", {}).get("default_status", "draft")
        # リスクチェック（キャプション＋画像内テキスト＋スライド文言を対象）
        post["risk"] = self._risk_check(post).to_dict()
        return post

    def _collect_texts(self, post: Dict[str, Any]) -> List[str]:
        texts = [post.get("title", ""), post.get("image_text", ""),
                 post.get("caption", ""), post.get("cta", "")]
        for s in post.get("slides", []):
            texts.append(s.get("image_text", ""))
            texts.append(s.get("note", ""))
        reel = post.get("reel")
        if reel:
            for sc in reel.get("scenes", []):
                texts.append(sc.get("on_screen", ""))
                texts.append(sc.get("narration", ""))
        story = post.get("story")
        if story:
            for fr in story.get("frames", []):
                texts.append(fr.get("image_text", ""))
        return [t for t in texts if t]

    def _risk_check(self, post: Dict[str, Any]):
        return self.checker.check_many(self._collect_texts(post))
