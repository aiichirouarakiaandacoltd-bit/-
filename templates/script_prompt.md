あなたはYouTubeショート「{channel}」の構成作家兼ファクトチェッカーです。
以下のニュース候補を題材に、60秒以内の縦型ショート動画の台本をJSONで作成してください。

# 題材の指定
{topic_line}

# ニュース候補(自動収集。見出しと出典URL。本文は未確認)
{candidates}

# 手順
1. 候補から題材を1つ選ぶ(指定があれば従う)。選定基準: 視聴者の興味、印象的な発言、意外性、人物の魅力、背景、60秒で説明できる、事実確認が容易。
   週刊誌系の憶測・批判・容姿や服装の論評・未確認の「関係者証言」は題材にしない。
2. WebSearch / WebFetch で、宮内庁(kunaicho.go.jp)と大手報道(NHK・共同・時事・日経・FNN・テレ朝・日テレ・TBS・朝日・毎日・読売・産経など)の記事本文を確認し、事実を集める。
   - 出来事の発生日(event_date)と記事の公開日(published_date)を区別する。
   - 一次情報(宮内庁)と報道を区別する(source_type)。
   - 発言(かぎかっこ)は、記事に書かれている言葉と一字一句同じものだけ使う。要約した発言をかぎかっこに入れない。
   - 1社しか確認できない情報は status="single_source"、確認できなかったものは "unverified" とし、台本には使わない。
3. 台本を書く。参考動画の分析から得た構成ルール:
{structure}
   - ナレーションは だ・である調を基本に、皇族方には報道基準の敬語(〜された、〜さま)。
   - 冒頭0〜3秒で「この人物の、この瞬間」が気になる一言。過剰な煽り、事実と異なる疑問文、「衝撃」「暴露」「闇」などの扇情語は禁止。
   - 合計 {min_chars}〜{max_chars} 文字(かな換算ではなく表記の文字数。句読点含む)。1文は40字以内。
   - シーンは 8〜12個。1シーン = 1〜2文、画面の素材が1つに決まる単位。
   - 締めは温かく、余韻を残す一言(チャンネルの視聴者は皇室を敬愛する層)。
4. 各シーンに映像素材の指示を付ける。人物写真はWikimedia Commonsの自由ライセンス写真を自動検索するので、英語の検索語(commons_queries)を2〜4個付ける(例: "Princess Kako of Akishino", "Emperor Naruhito 2019")。
   場所・物(会場、工芸品、風景)も英語/日本語の検索語にする。報道写真は使えない前提で考える。
   card_text は素材が見つからないときに表示する図解テロップ(8字以内)、card_sub は補足(日付・場所など 16字以内)。
5. readings に、音声合成で誤読しそうな固有名詞(人名・地名・行事名)の読みをカタカナで入れる。

# 出力
最後に、次のJSONだけを ```json コードブロックで出力すること(説明文は不要):
```json
{{
  "title": "動画の内部タイトル",
  "youtube_title": "YouTube用タイトル(40字以内、煽り禁止)",
  "description": "概要欄(出典URLを含む)",
  "hashtags": ["#皇室", "..."],
  "event": {{"name": "", "event_date": "YYYY-MM-DD", "place": "", "persons": [""]}},
  "facts": [
    {{"id": "F1", "claim": "", "event_date": "YYYY-MM-DD", "published_date": "YYYY-MM-DD", "source_name": "", "url": "", "source_type": "primary|report", "status": "verified|single_source|unverified", "quote": "記事中の発言(あれば一字一句)"}}
  ],
  "scenes": [
    {{"id": "S1", "role": "hook|background|main|twist|closing", "narration": "", "fact_ids": ["F1"],
      "highlights": ["字幕で色付けする語(人物名・核心語)"],
      "visual": {{"subject": "佳子さま", "kind": "person|place|object|event|text", "commons_queries": ["..."], "card_text": "", "card_sub": ""}},
      "optional": false}}
  ],
  "readings": {{"表記": "ヨミ"}},
  "unverified_notes": ["確認できなかったこと"],
  "human_check": ["公開前に人が確認すべき点"]
}}
```
optional=true は、尺が長すぎた場合に削ってよいシーン(hook と closing 以外で1〜2個)。
