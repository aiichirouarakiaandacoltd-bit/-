"""入力ファイル（YAML）の読み込みと検証.

PyYAML があればそれを使う。無い場合は最小限の自作パーサへ切り替える
（第0章 0-1）。自作パーサが対応するのは、本システムの設定ファイルと
入力ファイルで実際に使用している範囲に限る。

    key: value
    key: "quoted value"
    key: [a, b, c]
    key:
      - list item
    key:
      child: value
    # コメント

外部APIは呼ばない。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ENC = "utf-8"

try:  # pragma: no cover - 環境依存
    import yaml  # type: ignore

    HAS_PYYAML = True
except Exception:  # pragma: no cover - 環境依存
    yaml = None  # type: ignore
    HAS_PYYAML = False


# ---------------------------------------------------------------------
# 最小YAMLパーサ（PyYAML不在時のみ使用）
# ---------------------------------------------------------------------
# 対応する記法:
#   key: value / key: "quoted" / key: [a, b, c]
#   入れ子のマッピング
#   スカラーのリスト（- item）
#   マッピングのリスト（- key: value ＋ 続く同インデントのキー）
#   折りたたみスカラー（key: >- / >  / | / |-）
#   行コメント（# 以降）
# これ以外の記法（アンカー、複数ドキュメント、フロー形式のマッピング等）は
# 本システムの設定ファイルでは使用しない。
def _convert_scalar(raw: str) -> Any:
    text = raw.strip()
    if text == "" or text == "~" or text.lower() == "null":
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        inner = text[1:-1]
        if text[0] == '"':
            inner = inner.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
        return inner
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"-?\d+\.\d+", text):
        return float(text)
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_convert_scalar(part) for part in inner.split(",")]
    return text


def _unquote_key(key: str) -> str:
    key = key.strip()
    if len(key) >= 2 and key[0] == key[-1] and key[0] in "\"'":
        return key[1:-1]
    return key


def _strip_comment(line: str) -> str:
    """行末コメントを除去する（引用符内の # は残す）."""
    result = []
    quote: str | None = None
    for index, char in enumerate(line):
        if quote:
            result.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            result.append(char)
            continue
        if char == "#" and (index == 0 or line[index - 1] in " \t"):
            break
        result.append(char)
    return "".join(result).rstrip()


def _split_key_value(content: str) -> tuple[str, str] | None:
    """YAMLの規則に従い、": " または行末の ":" でのみキーと値を分ける.

    「SCAN:OFF」のように空白を伴わないコロンは区切りとみなさない。
    """
    quote: str | None = None
    for index, char in enumerate(content):
        if quote:
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            continue
        if char == ":" and (index + 1 == len(content) or content[index + 1] in " \t"):
            return content[:index], content[index + 1:].strip()
    return None


def _tokenize(text: str) -> list[tuple[int, str]]:
    """(インデント, 内容) の並びへ変換する。空行とコメント行は捨てる."""
    tokens: list[tuple[int, str]] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped_full = raw.strip()
        if not stripped_full or stripped_full.startswith("#"):
            index += 1
            continue
        line = _strip_comment(raw)
        if not line.strip():
            index += 1
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()

        # 折りたたみ／リテラルスカラー: key: >- のような行
        match = re.match(r"^(.+?):\s*([>|][-+]?)$", content)
        if match:
            key = match.group(1)
            block: list[str] = []
            index += 1
            while index < len(lines):
                following = lines[index]
                if not following.strip():
                    block.append("")
                    index += 1
                    continue
                following_indent = len(following) - len(following.lstrip(" "))
                if following_indent <= indent:
                    break
                block.append(following.strip())
                index += 1
            folded = " ".join(part for part in block if part)
            tokens.append((indent, f"{key}: {folded}"))
            continue

        tokens.append((indent, content))
        index += 1
    return tokens


def _parse_block(tokens: list[tuple[int, str]], position: int, indent: int) -> tuple[Any, int]:
    """indent 以上のインデントを持つ範囲を1つの値として解釈する."""
    if position >= len(tokens):
        return None, position

    if tokens[position][1].startswith("- "):
        return _parse_list(tokens, position, tokens[position][0])
    return _parse_mapping(tokens, position, indent)


def _parse_list(tokens: list[tuple[int, str]], position: int, indent: int) -> tuple[list, int]:
    items: list = []
    while position < len(tokens):
        current_indent, content = tokens[position]
        if current_indent < indent or not content.startswith("- "):
            break
        item = content[2:].strip()
        position += 1

        # "- key: value" 形式ならマッピング要素
        parts = _split_key_value(item) if not item.startswith(("\"", "'", "[")) else None
        if parts:
            key = _unquote_key(parts[0])
            value_text = parts[1]
            entry: dict = {}
            if value_text:
                entry[key] = _convert_scalar(value_text)
            else:
                child_indent = tokens[position][0] if position < len(tokens) else None
                if child_indent is not None and child_indent > current_indent:
                    value, position = _parse_block(tokens, position, child_indent)
                    entry[key] = value
                else:
                    entry[key] = None
            # 同じ要素に属する続きのキー（インデントが "- " の分だけ深い）
            while position < len(tokens):
                next_indent, next_content = tokens[position]
                if next_indent <= current_indent or next_content.startswith("- "):
                    break
                nested, position = _parse_mapping(tokens, position, next_indent)
                if isinstance(nested, dict):
                    entry.update(nested)
                else:
                    break
            items.append(entry)
        else:
            items.append(_convert_scalar(item))
    return items, position


def _parse_mapping(tokens: list[tuple[int, str]], position: int, indent: int) -> tuple[Any, int]:
    mapping: dict = {}
    while position < len(tokens):
        current_indent, content = tokens[position]
        if current_indent < indent:
            break
        if content.startswith("- "):
            break
        parts = _split_key_value(content)
        if not parts:
            position += 1
            continue

        key = _unquote_key(parts[0])
        value_text = parts[1]
        position += 1

        if value_text:
            mapping[key] = _convert_scalar(value_text)
            continue

        # 値が次行以降にある場合
        if position < len(tokens):
            next_indent, next_content = tokens[position]
            if next_indent > current_indent or (
                next_indent == current_indent and next_content.startswith("- ")
            ):
                value, position = _parse_block(tokens, position, next_indent)
                mapping[key] = value
                continue
        mapping[key] = None
    return mapping, position


def mini_yaml_load(text: str) -> dict:
    """PyYAML不在時に使用する簡易パーサ."""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    value, _ = _parse_block(tokens, 0, tokens[0][0])
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------------
# 公開関数
# ---------------------------------------------------------------------
def load_yaml(path: str | Path) -> dict:
    """YAMLファイルを読む。PyYAMLが無ければ簡易パーサを使う."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"ファイルが見つかりません: {path}")
    text = path.read_text(encoding=ENC)
    if HAS_PYYAML:
        data = yaml.safe_load(text)  # type: ignore[union-attr]
        return data if isinstance(data, dict) else {}
    return mini_yaml_load(text)


class ProjectInput:
    """project_input.yaml の内容を保持する."""

    def __init__(self, data: dict, source_path: Path):
        self.raw = data or {}
        self.source_path = Path(source_path)

    # -- 値の取り出し -------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        value = self.raw.get(key, default)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return default
        return value

    def get_list(self, key: str) -> list:
        value = self.raw.get(key)
        if value is None:
            return []
        if isinstance(value, list):
            return [item for item in value if item not in (None, "")]
        return [value]

    @property
    def project_slug(self) -> str:
        return str(self.get("project_slug", "") or "").strip()

    @property
    def project_name(self) -> str:
        return str(self.get("project_name", self.project_slug) or "")

    @property
    def sample_mode(self) -> bool:
        value = self.raw.get("sample_mode", False)
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "yes", "1", "はい")

    @property
    def target_length_min(self) -> int:
        return int(self.get("target_length_min", 12) or 12)

    @property
    def target_length_max(self) -> int:
        return int(self.get("target_length_max", 14) or 14)

    @property
    def shorts_count(self) -> int:
        return int(self.get("shorts_count", 1) or 1)

    # -- 検証 ---------------------------------------------------------
    def validate(self, required: list[str], recommended: list[str]) -> dict:
        """必須／推奨項目の欠落を検出する。処理は止めない."""
        errors: list[str] = []
        warnings: list[str] = []

        for key in required:
            if not self.get(key):
                errors.append(f"必須項目が未入力です: {key}")
        for key in recommended:
            if not self.get(key):
                warnings.append(f"推奨項目が未入力です: {key}")

        slug = self.project_slug
        if slug and not re.fullmatch(r"[A-Za-z0-9_\-]+", slug):
            errors.append(
                f"project_slug に使用できない文字が含まれています: {slug}"
                "（半角英数字・アンダースコア・ハイフンのみ）"
            )

        # 旧仕様の文字列型（例: target_length_minutes: 12-14）の混入検出
        if "target_length_minutes" in self.raw:
            errors.append(
                "target_length_minutes は廃止されました。"
                "target_length_min と target_length_max の数値2項目へ分離してください。"
            )

        try:
            if self.target_length_min > self.target_length_max:
                errors.append("target_length_min が target_length_max を超えています。")
        except (TypeError, ValueError):
            errors.append("target_length_min / target_length_max は数値で指定してください。")

        return {"errors": errors, "warnings": warnings}


def load_project_input(path: str | Path) -> ProjectInput:
    path = Path(path)
    return ProjectInput(load_yaml(path), path)


def load_approval(path: str | Path) -> dict:
    """approval.yaml を読む."""
    data = load_yaml(path)
    data.setdefault("approval_status", "pending")
    for key in ("approved_risks", "rejected_materials"):
        value = data.get(key)
        if value is None:
            data[key] = []
        elif not isinstance(value, list):
            data[key] = [value]
    return data
