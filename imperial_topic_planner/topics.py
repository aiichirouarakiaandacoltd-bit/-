"""企画候補の生成・採点・選別."""

from . import config as cfg


def _contains_prohibited(text):
    for expr in cfg.PROHIBITED_EXPRESSIONS:
        if expr in text:
            return True, expr
    return False, None


def _build_topic_candidates():
    """公式事実に基づく企画候補を生成する."""
    candidates = [
        {
            "id": "T001",
            "title": "愛子内親王殿下の成年皇族としての歩み――公式行事で見せた凛とした姿",
            "center_pin": "成年皇族として初めての単独公務から現在までの公式記録",
            "viewer_reason": "愛子さまの成長を見守ってきた視聴者にとって、公式行事での姿は感慨深い",
            "official_sources": [
                "宮内庁公式サイト（愛子内親王殿下のご日程）",
                "宮内庁公式YouTube（成年行事映像）",
                "NHK・主要報道（公務報道）",
            ],
            "long_reason": "成年から現在まで時系列で構成でき、7〜9分の情報量がある",
            "shorts_reason": "初の単独公務、ティアラ着用、記者会見など個別エピソードで切り出せる",
            "expected_emotion": "成長への感動、品格への敬意",
            "rights_risk": "低（公式映像・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 19,
                "official_facts": 18,
                "emotion": 14,
                "rights_safety": 14,
                "long_video": 9,
                "shorts": 9,
                "outsource": 9,
            },
        },
        {
            "id": "T002",
            "title": "天皇皇后両陛下の英国訪問――公式記録に残る温かな交流",
            "center_pin": "2024年英国公式訪問における両陛下の外交活動と交流の記録",
            "viewer_reason": "海外での両陛下の姿は視聴者の誇りと関心を集める",
            "official_sources": [
                "宮内庁公式サイト（英国訪問ご日程）",
                "外務省（公式訪問報告）",
                "英国王室公式（歓迎行事）",
                "NHK・主要報道",
            ],
            "long_reason": "出発から帰国まで日程順に構成でき、見どころが多い",
            "shorts_reason": "馬車パレード、晩餐会、チャールズ国王との握手など場面ごとに切り出せる",
            "expected_emotion": "誇り、外交への感謝、日英友好への温かさ",
            "rights_risk": "低（公式記録・テロップ中心、英国王室公式素材あり）",
            "priority": "A",
            "scores": {
                "viewer_fit": 18,
                "official_facts": 19,
                "emotion": 14,
                "rights_safety": 13,
                "long_video": 10,
                "shorts": 9,
                "outsource": 9,
            },
        },
        {
            "id": "T003",
            "title": "皇室の祈り――新年祝賀の儀と宮中祭祀に込められた思い",
            "center_pin": "天皇陛下が執り行う宮中祭祀と新年行事の公式記録",
            "viewer_reason": "日本の伝統と皇室の祈りに関心が高い層に響く",
            "official_sources": [
                "宮内庁公式サイト（祭祀・行事）",
                "宮内庁公式YouTube",
                "NHK（新年一般参賀中継）",
            ],
            "long_reason": "年間の祭祀を季節順に構成でき、深い解説が可能",
            "shorts_reason": "新年祝賀の儀、一般参賀、歌会始など個別行事で切り出せる",
            "expected_emotion": "厳かさ、日本の伝統への敬意",
            "rights_risk": "低（公式記録・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 18,
                "official_facts": 17,
                "emotion": 13,
                "rights_safety": 14,
                "long_video": 9,
                "shorts": 8,
                "outsource": 9,
            },
        },
        {
            "id": "T004",
            "title": "上皇ご夫妻の60年――公式記録で振り返る歩み",
            "center_pin": "ご結婚から上皇となられるまでの公式記録を時系列で辿る",
            "viewer_reason": "65歳以上の視聴者は上皇ご夫妻の時代を共に歩んだ世代",
            "official_sources": [
                "宮内庁公式サイト（上皇上皇后両陛下）",
                "NHK（退位関連報道）",
                "主要報道（ご結婚、即位、退位）",
            ],
            "long_reason": "60年の歩みを時代ごとに区切り、豊富な公式記録で構成できる",
            "shorts_reason": "ご結婚パレード、沖縄訪問、被災地お見舞いなど場面ごとに切り出せる",
            "expected_emotion": "懐かしさ、敬意、感謝",
            "rights_risk": "低（歴史的公式記録中心）",
            "priority": "B",
            "scores": {
                "viewer_fit": 20,
                "official_facts": 17,
                "emotion": 15,
                "rights_safety": 13,
                "long_video": 10,
                "shorts": 9,
                "outsource": 8,
            },
        },
        {
            "id": "T005",
            "title": "皇居の四季――一般参賀と乾通り公開で見る日本の美",
            "center_pin": "皇居で行われる一般公開行事と四季折々の風景の公式記録",
            "viewer_reason": "皇居の美しさと行事への関心は幅広い世代に共通する",
            "official_sources": [
                "宮内庁公式サイト（一般参賀・乾通り公開）",
                "環境省（皇居外苑）",
                "NHK・報道各社",
            ],
            "long_reason": "春夏秋冬の構成で7分以上を自然に構成できる",
            "shorts_reason": "桜の乾通り、紅葉、一般参賀の風景など季節ごとに切り出せる",
            "expected_emotion": "美しさへの感動、日本の誇り",
            "rights_risk": "低（風景・建造物・テロップ中心）",
            "priority": "B",
            "scores": {
                "viewer_fit": 17,
                "official_facts": 15,
                "emotion": 13,
                "rights_safety": 15,
                "long_video": 9,
                "shorts": 9,
                "outsource": 9,
            },
        },
        {
            "id": "T006",
            "title": "天皇陛下のお言葉――令和の時代に届けられたメッセージ",
            "center_pin": "令和以降の天皇陛下の公式お言葉・ご感想を読み解く",
            "viewer_reason": "陛下のお言葉に込められた思いを知りたい視聴者は多い",
            "official_sources": [
                "宮内庁公式サイト（天皇陛下のお言葉）",
                "宮内庁公式サイト（記者会見全文）",
                "NHK・主要報道",
            ],
            "long_reason": "即位、コロナ禍、英国訪問など節目ごとのお言葉で構成できる",
            "shorts_reason": "印象的なお言葉一つずつを取り上げ、背景とともに紹介できる",
            "expected_emotion": "感銘、共感、安心",
            "rights_risk": "低（公式テキスト・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 18,
                "official_facts": 19,
                "emotion": 14,
                "rights_safety": 15,
                "long_video": 9,
                "shorts": 9,
                "outsource": 9,
            },
        },
        {
            "id": "T007",
            "title": "皇室と被災地――公式記録に残るお見舞いの歩み",
            "center_pin": "東日本大震災、能登半島地震など被災地へのお見舞いの公式記録",
            "viewer_reason": "被災地に寄り添う皇室の姿は多くの視聴者の心に残っている",
            "official_sources": [
                "宮内庁公式サイト（お見舞いご日程）",
                "NHK・主要報道（お見舞い報道）",
                "自治体公式（訪問記録）",
            ],
            "long_reason": "複数の災害ごとに時系列で構成でき、深い内容になる",
            "shorts_reason": "個別の訪問エピソードごとに切り出せる",
            "expected_emotion": "感謝、温かさ、希望",
            "rights_risk": "低（公式記録・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 19,
                "official_facts": 17,
                "emotion": 15,
                "rights_safety": 13,
                "long_video": 9,
                "shorts": 9,
                "outsource": 8,
            },
        },
        {
            "id": "T008",
            "title": "令和の即位礼正殿の儀――公式記録で振り返る荘厳な一日",
            "center_pin": "2019年10月22日の即位礼正殿の儀の公式記録と式次第",
            "viewer_reason": "歴史的行事を改めて振り返りたい視聴者の需要がある",
            "official_sources": [
                "宮内庁公式サイト（即位の礼）",
                "首相官邸（即位礼関連）",
                "NHK（即位礼中継）",
                "外務省（参列各国）",
            ],
            "long_reason": "式次第に沿って構成でき、歴史的背景の解説も含められる",
            "shorts_reason": "高御座、十二単、参列各国元首など個別場面で切り出せる",
            "expected_emotion": "荘厳さ、誇り、感動",
            "rights_risk": "低（公式記録・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 18,
                "official_facts": 19,
                "emotion": 14,
                "rights_safety": 14,
                "long_video": 10,
                "shorts": 9,
                "outsource": 9,
            },
        },
        {
            "id": "T009",
            "title": "歌会始の儀――皇室と国民をつなぐ和歌の伝統",
            "center_pin": "毎年1月に行われる歌会始の儀の歴史と公式記録",
            "viewer_reason": "和歌と皇室の伝統に関心がある視聴者層に合致する",
            "official_sources": [
                "宮内庁公式サイト（歌会始）",
                "宮内庁公式サイト（お題・入選歌）",
                "NHK（歌会始中継）",
            ],
            "long_reason": "歴史、制度、近年のお歌を順に解説でき、文化的な深みがある",
            "shorts_reason": "天皇陛下・皇后陛下のお歌を個別に紹介できる",
            "expected_emotion": "文化への敬意、言葉の美しさへの感動",
            "rights_risk": "低（公式テキスト・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 17,
                "official_facts": 18,
                "emotion": 13,
                "rights_safety": 15,
                "long_video": 9,
                "shorts": 8,
                "outsource": 9,
            },
        },
        {
            "id": "T010",
            "title": "皇后陛下 雅子さまの外交――公式訪問で見せた国際親善の力",
            "center_pin": "雅子皇后陛下の国際親善活動と公式訪問の記録",
            "viewer_reason": "雅子さまの外交官時代からの歩みと皇后としての活躍に関心が高い",
            "official_sources": [
                "宮内庁公式サイト（皇后陛下ご日程）",
                "外務省（公式訪問記録）",
                "NHK・主要報道",
            ],
            "long_reason": "外交官時代、療養、復帰、英国訪問と時系列で豊富な構成が可能",
            "shorts_reason": "英国訪問、国連関連、各国との交流など場面ごとに切り出せる",
            "expected_emotion": "応援、敬意、誇り",
            "rights_risk": "低（公式記録・テロップ中心）",
            "priority": "A",
            "scores": {
                "viewer_fit": 19,
                "official_facts": 17,
                "emotion": 14,
                "rights_safety": 13,
                "long_video": 9,
                "shorts": 9,
                "outsource": 8,
            },
        },
        {
            "id": "T011",
            "title": "正倉院展と皇室ゆかりの文化財――受け継がれる日本の宝",
            "center_pin": "正倉院宝物と皇室ゆかりの文化財の公式記録",
            "viewer_reason": "日本文化と皇室の関わりに興味がある視聴者に響く",
            "official_sources": [
                "宮内庁公式サイト（正倉院・三の丸尚蔵館）",
                "奈良国立博物館（正倉院展）",
                "文化庁",
            ],
            "long_reason": "代表的な宝物を紹介しながら歴史的背景を解説できる",
            "shorts_reason": "個別の宝物や展示品ごとに切り出せる",
            "expected_emotion": "文化への誇り、歴史の重み",
            "rights_risk": "低（公的機関の資料・テロップ中心）",
            "priority": "B",
            "scores": {
                "viewer_fit": 16,
                "official_facts": 17,
                "emotion": 12,
                "rights_safety": 14,
                "long_video": 9,
                "shorts": 8,
                "outsource": 8,
            },
        },
        {
            "id": "T012",
            "title": "皇室の週刊誌報道を検証する――事実と憶測の境界線",
            "center_pin": "週刊誌報道と公式発表の比較検証",
            "viewer_reason": "週刊誌報道への不信感を持つ視聴者に需要がある",
            "official_sources": [],
            "long_reason": "対立構造になりやすく、中立的な構成が困難",
            "shorts_reason": "個別記事の検証は煽りに寄りやすい",
            "expected_emotion": "怒り、不満（ネガティブ寄り）",
            "rights_risk": "高（週刊誌記事の引用、名誉毀損リスク）",
            "priority": "C",
            "scores": {
                "viewer_fit": 14,
                "official_facts": 5,
                "emotion": 8,
                "rights_safety": 4,
                "long_video": 7,
                "shorts": 6,
                "outsource": 5,
            },
        },
        {
            "id": "T013",
            "title": "皇位継承問題の全容――制度と議論を中立に解説",
            "center_pin": "皇位継承に関する制度と有識者会議の議論",
            "viewer_reason": "制度への関心はあるが、対立煽りを嫌う層が多い",
            "official_sources": [
                "首相官邸（有識者会議報告書）",
                "衆議院・参議院（皇室典範関連）",
            ],
            "long_reason": "制度解説として構成可能だが、対立軸が生まれやすい",
            "shorts_reason": "制度のポイントを短くまとめられるが、断片化で誤解を招きやすい",
            "expected_emotion": "関心、不安（慎重なテーマ）",
            "rights_risk": "中（政治的議論との境界が曖昧）",
            "priority": "C",
            "scores": {
                "viewer_fit": 13,
                "official_facts": 15,
                "emotion": 8,
                "rights_safety": 9,
                "long_video": 8,
                "shorts": 5,
                "outsource": 6,
            },
        },
    ]

    for c in candidates:
        c["total_score"] = sum(c["scores"].values())
        has_prohibited, expr = _contains_prohibited(c["title"])
        c["has_prohibited"] = has_prohibited
        c["prohibited_expr"] = expr

    return candidates


def select_topics(candidates):
    """候補を採用・保留・不採用に振り分ける."""
    selected = []
    rejected = []

    for c in candidates:
        if c["has_prohibited"]:
            c["status"] = "不採用"
            c["reject_reason"] = f"禁止表現「{c['prohibited_expr']}」を含む"
            rejected.append(c)
            continue

        if not c["official_sources"]:
            c["status"] = "不採用"
            c["reject_reason"] = "公式根拠候補が空欄"
            rejected.append(c)
            continue

        if c["total_score"] < cfg.PASS_THRESHOLD:
            c["status"] = "不採用"
            c["reject_reason"] = f"採点{c['total_score']}点（基準{cfg.PASS_THRESHOLD}点未満）"
            rejected.append(c)
            continue

        if c["rights_risk"].startswith("高"):
            c["status"] = "不採用"
            c["reject_reason"] = f"権利リスクが高い（{c['rights_risk']}）"
            rejected.append(c)
            continue

        c["status"] = "採用"
        selected.append(c)

    selected.sort(key=lambda x: x["total_score"], reverse=True)
    return selected, rejected


def generate_candidates():
    """企画候補の生成・選別を実行して結果を返す."""
    candidates = _build_topic_candidates()
    selected, rejected = select_topics(candidates)
    return {
        "candidates": candidates,
        "selected": selected,
        "rejected": rejected,
    }
