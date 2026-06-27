"""企画候補の生成・採点・選別（入力データ駆動版）."""

from . import config as cfg
from .input_loader import extract_themes_from_references, compute_reference_demand


def _contains_prohibited(text):
    for expr in cfg.PROHIBITED_EXPRESSIONS:
        if expr in text:
            return True, expr
    return False, None


def _is_banned(title, keywords, banned_themes):
    """採用禁止テーマに該当するか."""
    for ban in banned_themes:
        if ban in title:
            return True, ban
        for kw in keywords:
            if ban in kw:
                return True, ban
    return False, None


def _score_topic(idea, input_data, theme_demand):
    """入力データに基づいて10軸スコアを算出."""
    scores = {}
    keywords = idea.get("theme_keywords", [])

    # 1. 需要スコア: 参考動画のテーマ一致度＋需要指標
    demand = 0
    matched_refs = []
    for vid in input_data.get("reference_videos", []):
        vid_theme = vid.get("theme", "")
        if any(kw in vid_theme or vid_theme in kw for kw in keywords if kw and vid_theme):
            matched_refs.append(vid)
        elif any(kw in vid.get("title", "") for kw in keywords if kw):
            matched_refs.append(vid)
    if matched_refs:
        demands = [compute_reference_demand(v) for v in matched_refs]
        demand = round(min(sum(demands) / len(demands) + len(demands) * 0.5, 10), 1)
    else:
        demand = idea.get("demand_override", 4)
    scores["demand"] = min(demand, 10)

    # 2. 競合伸長スコア: 競合チャンネルの同テーマ動画の伸び
    comp_score = 0
    for vid in matched_refs:
        subs = vid.get("subscribers_at_publish", 0)
        views = vid.get("views", 0)
        if subs > 0 and views / subs > 5:
            comp_score += 3
        elif subs > 0 and views / subs > 2:
            comp_score += 2
        else:
            comp_score += 1
    scores["competitor_growth"] = min(round(comp_score, 1), 10)
    if not matched_refs:
        scores["competitor_growth"] = idea.get("competitor_growth_override", 3)

    # 3. 少登録者でも伸びる再現性
    repro = 0
    small_ch_hits = [v for v in matched_refs
                     if v.get("subscribers_at_publish", 999999) < 50000
                     and v.get("views", 0) > 10000]
    if small_ch_hits:
        repro = min(len(small_ch_hits) * 3 + 2, 10)
    else:
        repro = idea.get("reproducibility_override", 4)
    scores["reproducibility"] = min(repro, 10)

    # 4. 皇室チャンネル適合性
    fit = 7
    channel_keywords = ["皇室", "天皇", "皇后", "愛子", "宮内庁", "皇居",
                         "祭祀", "即位", "行幸", "公務", "皇族", "内親王"]
    for kw in keywords:
        if any(ck in kw for ck in channel_keywords):
            fit += 1
    scores["channel_fit"] = min(fit, 10)

    # 5. 公式根拠の有無
    source_urls = idea.get("official_source_urls", [])
    available_sources = {s.get("url", "") for s in input_data.get("official_sources", [])}
    matched_sources = [u for u in source_urls if u in available_sources]
    if source_urls:
        evidence = min(len(matched_sources) * 3 + len(source_urls) * 1, 10)
    else:
        evidence = 0
    scores["official_evidence"] = min(evidence, 10)

    # 6. 権利リスク（高→低スコア）
    risk_text = idea.get("rights_risk", "中")
    if risk_text.startswith("低"):
        scores["rights_safety"] = 9
    elif risk_text.startswith("中"):
        scores["rights_safety"] = 5
    else:
        scores["rights_safety"] = 2

    # 7. 65歳以上女性への適合性
    senior_keywords = ["愛子", "雅子", "皇后", "天皇", "令和", "平成",
                        "被災地", "お見舞い", "祈り", "伝統", "行事"]
    senior = 5
    for kw in keywords:
        if any(sk in kw for sk in senior_keywords):
            senior += 1
    scores["senior_fit"] = min(senior, 10)

    # 8. 長尺化可否
    long_ok = 7 if idea.get("long_reason") else 3
    scores["long_video"] = min(long_ok, 10)

    # 9. Shorts展開可否
    shorts_ok = 7 if idea.get("shorts_reason") else 3
    scores["shorts_potential"] = min(shorts_ok, 10)

    # 10. 推定制作コスト（テロップ中心=安い=高スコア）
    if risk_text.startswith("低"):
        scores["production_cost"] = 8
    elif risk_text.startswith("中"):
        scores["production_cost"] = 6
    else:
        scores["production_cost"] = 3

    return scores


def generate_candidates_from_input(input_data):
    """入力データから企画候補を生成・採点・選別."""
    banned = input_data.get("banned_themes", [])
    theme_demand = extract_themes_from_references(input_data)
    candidates = []

    for i, idea in enumerate(input_data.get("topic_ideas", [])):
        topic_id = f"T{i + 1:03d}"
        title = idea["title"]
        keywords = idea.get("theme_keywords", [])

        has_prohibited, prohibited_expr = _contains_prohibited(title)
        is_banned, banned_expr = _is_banned(title, keywords, banned)

        scores = _score_topic(idea, input_data, theme_demand)
        total = sum(scores.values())

        source_urls = idea.get("official_source_urls", [])
        available_sources = input_data.get("official_sources", [])
        official_sources_display = []
        for url in source_urls:
            matched = [s for s in available_sources if s.get("url") == url]
            if matched:
                official_sources_display.append(f"{matched[0].get('name', '')} ({url})")
            else:
                official_sources_display.append(f"未確認URL ({url})")
        if not source_urls:
            for s in available_sources:
                for kw in keywords:
                    if kw and kw in s.get("name", ""):
                        official_sources_display.append(f"{s['name']} ({s.get('url', '')})")
                        break

        candidate = {
            "id": topic_id,
            "title": title,
            "center_pin": idea.get("center_pin", ""),
            "theme_keywords": keywords,
            "viewer_reason": idea.get("viewer_reason", ""),
            "official_sources": official_sources_display,
            "official_source_urls": source_urls,
            "long_reason": idea.get("long_reason", ""),
            "shorts_reason": idea.get("shorts_reason", ""),
            "expected_emotion": idea.get("expected_emotion", ""),
            "rights_risk": idea.get("rights_risk", "中"),
            "notes": idea.get("notes", ""),
            "scores": scores,
            "total_score": round(total, 1),
            "has_prohibited": has_prohibited,
            "prohibited_expr": prohibited_expr,
            "is_banned": is_banned,
            "banned_expr": banned_expr,
            "matched_reference_count": len([
                v for v in input_data.get("reference_videos", [])
                if any(kw in v.get("theme", "") or kw in v.get("title", "")
                       for kw in keywords if kw)
            ]),
            "data_source": "input",
        }
        candidates.append(candidate)

    return select_topics(candidates, banned)


def select_topics(candidates, banned_themes):
    """候補を採用・保留・不採用に振り分ける."""
    selected = []
    held = []
    rejected = []

    for c in candidates:
        if c["has_prohibited"]:
            c["status"] = "不採用"
            c["reject_reason"] = f"禁止表現「{c['prohibited_expr']}」を含む"
            rejected.append(c)
            continue

        if c["is_banned"]:
            c["status"] = "不採用"
            c["reject_reason"] = f"採用禁止テーマ「{c['banned_expr']}」に該当"
            rejected.append(c)
            continue

        if c["scores"].get("official_evidence", 0) == 0 and not c.get("official_source_urls"):
            c["status"] = "不採用"
            c["reject_reason"] = "公式根拠なし"
            rejected.append(c)
            continue

        if c["scores"].get("rights_safety", 10) <= 3:
            c["status"] = "不採用"
            c["reject_reason"] = f"権利リスクが高い（{c['rights_risk']}）"
            rejected.append(c)
            continue

        is_clickbait = c["has_prohibited"] or c["scores"].get("demand", 0) > 7 and c["scores"].get("official_evidence", 0) < 3
        if is_clickbait:
            c["status"] = "不採用"
            c["reject_reason"] = "煽り依存（需要は高いが公式根拠が不足）"
            rejected.append(c)
            continue

        if c["total_score"] < cfg.HOLD_THRESHOLD:
            c["status"] = "不採用"
            c["reject_reason"] = f"採点{c['total_score']}点（基準{cfg.HOLD_THRESHOLD}点未満）"
            rejected.append(c)
            continue

        if c["total_score"] < cfg.PASS_THRESHOLD:
            c["status"] = "保留"
            c["reject_reason"] = f"採点{c['total_score']}点（採用基準{cfg.PASS_THRESHOLD}点未満、保留）"
            held.append(c)
            continue

        c["status"] = "採用"
        c["reject_reason"] = ""
        selected.append(c)

    selected.sort(key=lambda x: x["total_score"], reverse=True)
    held.sort(key=lambda x: x["total_score"], reverse=True)
    return {
        "candidates": candidates,
        "selected": selected,
        "held": held,
        "rejected": rejected,
    }


# --- テスト用サンプル（production判定には使わない） ---

def _build_test_sample_input():
    """テスト専用のサンプル入力データを返す."""
    return {
        "competitor_channels": [
            {"url": "https://www.youtube.com/@example-imperial", "name": "皇室解説Ch"},
        ],
        "reference_videos": [
            {
                "url": "https://www.youtube.com/watch?v=test1",
                "title": "愛子さま成年の歩み",
                "channel": "皇室解説Ch",
                "theme": "愛子さま",
                "views": 200000,
                "published": "2026-05-01",
                "subscribers_at_publish": 8000,
                "ctr_estimate": 9.5,
                "avg_watch_time_pct": 48,
                "is_shorts": False,
                "drove_long_views": True,
            },
            {
                "url": "https://www.youtube.com/watch?v=test2",
                "title": "天皇皇后両陛下 英国ご訪問",
                "channel": "皇室ニュース",
                "theme": "英国訪問",
                "views": 350000,
                "published": "2026-04-20",
                "subscribers_at_publish": 15000,
                "ctr_estimate": 11.0,
                "avg_watch_time_pct": 52,
                "is_shorts": False,
                "drove_long_views": True,
            },
            {
                "url": "https://www.youtube.com/watch?v=test3",
                "title": "皇居の桜 一般公開",
                "channel": "日本文化Ch",
                "theme": "皇居",
                "views": 80000,
                "published": "2026-04-05",
                "subscribers_at_publish": 3000,
                "ctr_estimate": 7.0,
                "avg_watch_time_pct": 40,
                "is_shorts": False,
                "drove_long_views": False,
            },
        ],
        "own_channel_videos": [
            {
                "url": "https://www.youtube.com/watch?v=own1",
                "title": "愛子と敬宮の由来",
                "views": 12000,
                "published": "2026-05-15",
                "ctr": 6.5,
                "avg_watch_time_pct": 55,
                "repeat_viewers_pct": 35,
            },
        ],
        "banned_themes": [
            "皇位継承問題",
            "週刊誌検証",
        ],
        "official_sources": [
            {"url": "https://www.kunaicho.go.jp/activity/gonittei/01/h01.html",
             "name": "宮内庁 天皇陛下ご日程", "type": "宮内庁"},
            {"url": "https://www.kunaicho.go.jp/activity/gonittei/02/h02.html",
             "name": "宮内庁 皇后陛下ご日程", "type": "宮内庁"},
            {"url": "https://www.kunaicho.go.jp/activity/gonittei/05/h05.html",
             "name": "宮内庁 愛子内親王殿下ご日程", "type": "宮内庁"},
            {"url": "https://www.youtube.com/@KunijichoJP",
             "name": "宮内庁公式YouTube", "type": "公式SNS"},
            {"url": "https://www.mofa.go.jp/mofaj/",
             "name": "外務省", "type": "公的機関"},
        ],
        "topic_ideas": [
            {
                "title": "愛子内親王殿下の成年皇族としての歩み――公式行事で見せた凛とした姿",
                "center_pin": "成年皇族として初めての単独公務から現在までの公式記録",
                "theme_keywords": ["愛子さま", "成年", "公務"],
                "official_source_urls": [
                    "https://www.kunaicho.go.jp/activity/gonittei/05/h05.html",
                    "https://www.youtube.com/@KunijichoJP",
                ],
                "viewer_reason": "愛子さまの成長を見守ってきた視聴者にとって、公式行事での姿は感慨深い",
                "long_reason": "成年から現在まで時系列で構成でき、7〜9分の情報量がある",
                "shorts_reason": "初の単独公務、ティアラ着用、記者会見など個別エピソードで切り出せる",
                "expected_emotion": "成長への感動、品格への敬意",
                "rights_risk": "低",
            },
            {
                "title": "天皇皇后両陛下の英国訪問――公式記録に残る温かな交流",
                "center_pin": "2024年英国公式訪問における両陛下の外交活動と交流の記録",
                "theme_keywords": ["英国訪問", "天皇", "皇后", "外交"],
                "official_source_urls": [
                    "https://www.kunaicho.go.jp/activity/gonittei/01/h01.html",
                    "https://www.mofa.go.jp/mofaj/",
                ],
                "viewer_reason": "海外での両陛下の姿は視聴者の誇りと関心を集める",
                "long_reason": "出発から帰国まで日程順に構成でき、見どころが多い",
                "shorts_reason": "馬車パレード、晩餐会、チャールズ国王との握手など場面ごとに切り出せる",
                "expected_emotion": "誇り、外交への感謝、日英友好への温かさ",
                "rights_risk": "低",
            },
            {
                "title": "皇居の四季――一般参賀と乾通り公開で見る日本の美",
                "center_pin": "皇居で行われる一般公開行事と四季折々の風景の公式記録",
                "theme_keywords": ["皇居", "一般参賀", "四季"],
                "official_source_urls": [
                    "https://www.kunaicho.go.jp/activity/gonittei/01/h01.html",
                ],
                "viewer_reason": "皇居の美しさと行事への関心は幅広い世代に共通する",
                "long_reason": "春夏秋冬の構成で7分以上を自然に構成できる",
                "shorts_reason": "桜の乾通り、紅葉、一般参賀の風景など季節ごとに切り出せる",
                "expected_emotion": "美しさへの感動、日本の誇り",
                "rights_risk": "低",
            },
            {
                "title": "皇位継承問題の全容――制度と議論を中立に解説",
                "center_pin": "皇位継承に関する制度と有識者会議の議論",
                "theme_keywords": ["皇位継承問題"],
                "official_source_urls": [],
                "viewer_reason": "制度への関心はあるが対立煽りを嫌う層が多い",
                "long_reason": "制度解説として構成可能だが対立軸が生まれやすい",
                "shorts_reason": "断片化で誤解を招きやすい",
                "expected_emotion": "関心、不安",
                "rights_risk": "中",
            },
            {
                "title": "皇室の週刊誌報道を検証する",
                "center_pin": "週刊誌報道と公式発表の比較",
                "theme_keywords": ["週刊誌検証"],
                "official_source_urls": [],
                "viewer_reason": "週刊誌への不信感",
                "long_reason": "対立構造になりやすい",
                "shorts_reason": "煽りに寄りやすい",
                "expected_emotion": "怒り、不満",
                "rights_risk": "高",
            },
        ],
    }
