"""Video editing and thumbnail instruction generator for outsourcing packages."""
from pathlib import Path

import config as cfg


def generate_video_instructions(topic, research_data, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "video_editing_instructions.md"

    long_specs = cfg.VIDEO_SPECS["long"]
    shorts_specs = cfg.VIDEO_SPECS["shorts"]
    vv = cfg.VOICEVOX_SETTINGS

    confirmed_facts = [f for f in research_data.get("facts", [])
                       if f.get("status") == cfg.FactStatus.CONFIRMED]

    lines = []
    lines.append("# 動画制作指示書")
    lines.append("")
    lines.append(f"## 企画テーマ")
    lines.append(f"{topic}")
    lines.append("")
    lines.append("## 動画の目的")
    lines.append(f"チャンネル「{cfg.CHANNEL_NAME}」の方針「{cfg.CHANNEL_PROMISE}」に基づき、")
    lines.append(f"公式資料をもとに{topic}を解説する動画を制作する。")
    lines.append("")
    lines.append("## 想定視聴者")
    lines.append(f"{cfg.TARGET_AUDIENCE}")
    lines.append("")

    lines.append("## 長尺動画仕様")
    lines.append(f"- 画面比率: 16:9")
    lines.append(f"- 解像度: {long_specs['width']}×{long_specs['height']}")
    lines.append(f"- フレームレート: {long_specs['fps']}fps")
    lines.append(f"- 想定尺: {long_specs['duration_min_seconds']//60}～{long_specs['duration_max_seconds']//60}分")
    lines.append("")

    lines.append("## Shorts動画仕様")
    lines.append(f"- 画面比率: 9:16")
    lines.append(f"- 解像度: {shorts_specs['width']}×{shorts_specs['height']}")
    lines.append(f"- フレームレート: {shorts_specs['fps']}fps")
    lines.append(f"- 想定尺: {shorts_specs['duration_min_seconds']}～{shorts_specs['duration_max_seconds']}秒")
    lines.append("")

    lines.append("## 章構成")
    lines.append("")
    lines.append("台本（long_script.txt）に記載の章立てに従ってください。")
    lines.append("各章の素材候補は material_urls.csv を参照してください。")
    lines.append("")

    if confirmed_facts:
        lines.append("### 主なパート")
        for i, fact in enumerate(confirmed_facts[:5], 1):
            lines.append(f"{i}. {fact.get('claim', '')[:60]}...")
        lines.append("")

    lines.append("## 字幕ルール")
    lines.append("- 書体: 太字ゴシック")
    lines.append("- 黒フチ付き")
    lines.append("- サイズ: 大きめ（65歳以上のスマートフォン視聴を優先）")
    lines.append("- 行数: 2行以内")
    lines.append("- 文字化け禁止（日本語フォント必須）")
    lines.append("- 長尺: 画面下部中央に配置（MarginV=60推奨）")
    lines.append("- Shorts: 下部UI・右側UIを避けて配置")
    lines.append("")

    lines.append("## ナレーションルール")
    lines.append(f"- TTS: VOICEVOX {vv['speaker_name']}")
    lines.append(f"- 速度: {vv['speed']}")
    lines.append("- 年号・固有名詞は聞き取りやすく調整")
    lines.append("- 別話者へ変更しないこと")
    lines.append("")

    lines.append("## 画面切り替え")
    lines.append("- シンプルなフェード切り替えを基本とする")
    lines.append("- 過度なエフェクトは使用しない")
    lines.append("- 画像にはゆるやかなズームまたは横移動を適用")
    lines.append("")

    lines.append("## イメージ表記ルール")
    lines.append("- 一般風景・建物・背景素材は「イメージ」ラベルを表示")
    lines.append("- 実在の公式記録写真には「イメージ」と表示しないこと")
    lines.append("- 両者を混同しないこと")
    lines.append("")

    lines.append("## BGM")
    lines.append(f"- ファイル名: {cfg.BGM_SETTINGS['file_name']}")
    lines.append(f"- 提供元: {cfg.BGM_SETTINGS['provider']}")
    lines.append("- 別BGMへ勝手に変更しないこと")
    lines.append("- ナレーションを妨げない音量")
    lines.append("- 冒頭フェードイン、末尾フェードアウト")
    lines.append("- 実際に使用した場合のみクレジット記載")
    lines.append("")

    lines.append("## 禁止素材")
    for item in cfg.PROHIBITED_IMAGE_TYPES:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## 禁止表現")
    for item in cfg.PROHIBITED_EXPRESSIONS[:10]:
        lines.append(f"- {item}")
    lines.append("")

    lines.append("## 完成前確認事項")
    lines.append("- 字幕の誤字脱字チェック")
    lines.append("- ナレーションと字幕の同期確認")
    lines.append("- 素材の権利状態確認")
    lines.append("- BGMクレジット確認")
    lines.append("- 禁止表現が含まれていないか確認")
    lines.append("")

    lines.append("## 進捗確認")
    lines.append("進捗確認は原則2回までとします。")
    lines.append("1. 制作途中の方向性確認")
    lines.append("2. 完成前確認")
    lines.append("外注者へ不要な調査・報告・作業を増やさないこと。")
    lines.append("")

    lines.append("※ 価格・納期・契約条件はこの指示書には記載しません。")

    content = "\n".join(lines)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def generate_thumbnail_instructions(topic, research_data, output_dir):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / "thumbnail_instructions.md"

    lines = []
    lines.append("# サムネイル制作指示書")
    lines.append("")
    lines.append(f"## 企画テーマ")
    lines.append(f"{topic}")
    lines.append("")

    lines.append("## サムネイルの狙い")
    lines.append(f"- 「{topic}」の内容を一瞬で伝える")
    lines.append(f"- {cfg.TARGET_AUDIENCE}がスマートフォンでクリックしたくなる")
    lines.append("- 品格を保ちつつ知的好奇心を刺激する")
    lines.append("")

    lines.append("## 共通仕様")
    lines.append("- 人物は2～3人まで")
    lines.append("- スマートフォンで一瞬で理解できるデザイン")
    lines.append("- 文字: 太い黒フチ")
    lines.append("- 上段文字: 黄色系")
    lines.append("- 下段文字: 赤または金系を基本")
    lines.append("- 品格を損なう煽りは禁止")
    lines.append("- 人物表情をAIで変更しない")
    lines.append("- 動画内にない出来事を示唆しない")
    lines.append("- 涙・怒り・対立を誇張しない")
    lines.append("")

    lines.append("## 案A（王道案）")
    lines.append("")
    lines.append("分かりやすく、人物と出来事を明示する案")
    lines.append("")
    lines.append(f"### 文字案")
    short_topic = topic.split("――")[0] if "――" in topic else topic
    lines.append(f"- 上段: 「{short_topic[:15]}」")
    lines.append(f"- 下段: 「公式記録から読み解く」")
    lines.append("")
    lines.append("### 画像構成")
    lines.append("- テーマに関連する公式画像または風景")
    lines.append("- 使用候補画像URLは material_urls.csv を参照")
    lines.append("- 画像使用には権利確認が必要")
    lines.append("")

    lines.append("## 案B（知的好奇心重視案）")
    lines.append("")
    lines.append("文化・歴史・知識への関心を重視する案")
    lines.append("")
    lines.append(f"### 文字案")
    lines.append(f"- 上段: 「知っていますか？」")
    lines.append(f"- 下段: 「{short_topic[:20]}」")
    lines.append("")
    lines.append("### 画像構成")
    lines.append("- 歴史的資料や文化的背景を感じさせる画像")
    lines.append("- 人物よりもテーマの深さを伝える")
    lines.append("")

    lines.append("## 2案の違い")
    lines.append("- 案A: CTR重視、直感的にテーマが伝わる")
    lines.append("- 案B: 視聴者の知的好奇心に訴える、差別化を図る")
    lines.append("")

    lines.append("## 避ける表現")
    lines.append("- 過度な煽り文言")
    lines.append("- 動画内容と異なる印象を与える画像")
    lines.append("- 対立・怒り・涙の誇張")
    lines.append("- AI生成の人物画像")
    lines.append("")

    lines.append("※ 画像自体の自動生成は行いません。")
    lines.append("※ 価格・納期・契約条件はこの指示書には記載しません。")

    content = "\n".join(lines)
    file_path.write_text(content, encoding="utf-8")
    return file_path
