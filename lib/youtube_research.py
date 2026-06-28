"""YouTube動画調査モジュール - YouTube Data API経由で候補動画を検索・取得"""
import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_config():
    path = os.path.join(BASE_DIR, "config", "research_config.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _default_config()


def _default_config():
    return {
        "research_days": 90,
        "candidate_limit": 100,
        "search_queries_ja": [
            "河村勇輝 ノールックパス",
            "八村塁 ダンク",
            "レブロン ダンク",
            "カリー スリーポイント",
            "ウェンバンヤマ ブロック",
            "富樫勇樹 ドライブ",
            "富永啓生 シュート",
            "渡邊雄太 ディフェンス",
            "比江島慎 ステップ",
            "NBA スーパープレー",
            "NBA クラッチプレー",
            "Bリーグ ハイライト",
            "NBA ダンク 2025",
            "NBA ブロック ベスト",
            "NBA アシスト ノールック",
            "日本人 NBA 選手",
        ],
        "search_queries_en": [
            "NBA best assists",
            "NBA insane blocks",
            "NBA clutch plays",
            "NBA best dunks highlights",
            "Yuki Kawamura no look pass",
            "Rui Hachimura dunk",
            "Victor Wembanyama block",
            "Steph Curry deep three",
            "B League highlights",
            "NBA step back three",
        ],
    }


class YouTubeResearchClient:
    """YouTube Data API v3を使用した動画調査クライアント"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("YOUTUBE_API_KEY")
        self.config = _load_config()
        self._api_available = False
        if self.api_key:
            try:
                from googleapiclient.discovery import build
                self._youtube = build("youtube", "v3", developerKey=self.api_key)
                self._api_available = True
            except ImportError:
                self._youtube = None
            except Exception:
                self._youtube = None

    @property
    def is_available(self):
        return self._api_available and self._youtube is not None

    def search_videos(self, query, max_results=25, published_after_days=None):
        """YouTube検索を実行し、候補動画リストを返す"""
        if not self.is_available:
            return {"query": query, "results": [], "error": "YouTube API未設定またはライブラリ不足"}

        days = published_after_days or self.config.get("research_days", 90)
        after = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%dT00:00:00Z")

        try:
            request = self._youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=min(max_results, 50),
                order="viewCount",
                publishedAfter=after,
                relevanceLanguage="ja",
            )
            response = request.execute()
            video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
            if not video_ids:
                return {"query": query, "results": [], "error": None}

            stats_request = self._youtube.videos().list(
                id=",".join(video_ids),
                part="snippet,statistics,contentDetails",
            )
            stats_response = stats_request.execute()

            results = []
            for item in stats_response.get("items", []):
                snippet = item["snippet"]
                stats = item.get("statistics", {})
                results.append({
                    "video_id": item["id"],
                    "url": f"https://www.youtube.com/watch?v={item['id']}",
                    "title": snippet.get("title"),
                    "channel_name": snippet.get("channelTitle"),
                    "published_at": snippet.get("publishedAt"),
                    "duration": item.get("contentDetails", {}).get("duration"),
                    "view_count": int(stats.get("viewCount", 0)),
                    "like_count": int(stats.get("likeCount", 0)),
                    "comment_count": int(stats.get("commentCount", 0)),
                    "channel_subscriber_count": None,
                    "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                    "description": snippet.get("description", ""),
                    "search_query": query,
                })
            return {"query": query, "results": results, "error": None}

        except Exception as e:
            return {"query": query, "results": [], "error": str(e)}

    def run_full_research(self):
        """全検索クエリを実行し、候補動画を集約"""
        all_results = []
        seen_ids = set()
        queries = self.config["search_queries_ja"] + self.config["search_queries_en"]

        for query in queries:
            result = self.search_videos(query)
            for video in result.get("results", []):
                vid = video["video_id"]
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    all_results.append(video)

            if len(all_results) >= self.config.get("candidate_limit", 100):
                break

        return {
            "total_candidates": len(all_results),
            "queries_executed": len(queries),
            "api_available": self.is_available,
            "candidates": all_results[:self.config.get("candidate_limit", 100)],
        }


class FixtureResearchClient:
    """テスト・オフライン用のfixture研究クライアント"""

    def __init__(self):
        self.config = _load_config()

    @property
    def is_available(self):
        return True

    def search_videos(self, query, max_results=25, published_after_days=None):
        return {
            "query": query,
            "results": _generate_fixture_results(query),
            "error": None,
            "fixture": True,
        }

    def run_full_research(self):
        all_results = []
        seen_ids = set()
        queries = self.config["search_queries_ja"][:5] + self.config["search_queries_en"][:3]
        for query in queries:
            result = self.search_videos(query)
            for video in result.get("results", []):
                vid = video["video_id"]
                if vid not in seen_ids:
                    seen_ids.add(vid)
                    all_results.append(video)
        return {
            "total_candidates": len(all_results),
            "queries_executed": len(queries),
            "api_available": False,
            "fixture": True,
            "candidates": all_results,
        }


def _generate_fixture_results(query):
    """クエリに基づいたfixtureデータを生成"""
    fixtures = {
        "河村勇輝": [
            {"video_id": "fixture_kw001", "title": "河村勇輝 驚異のノールックパス集",
             "channel_name": "Basketball JP", "view_count": 850000, "like_count": 12000,
             "comment_count": 450, "published_at": "2026-04-15T00:00:00Z"},
            {"video_id": "fixture_kw002", "title": "河村勇輝 Bリーグ2026シーズンベストプレー",
             "channel_name": "B.LEAGUE Official", "view_count": 1200000, "like_count": 25000,
             "comment_count": 800, "published_at": "2026-05-01T00:00:00Z"},
        ],
        "NBA": [
            {"video_id": "fixture_nba001", "title": "Top 10 NBA Assists - June 2026",
             "channel_name": "NBA", "view_count": 5000000, "like_count": 80000,
             "comment_count": 3000, "published_at": "2026-06-01T00:00:00Z"},
            {"video_id": "fixture_nba002", "title": "Best Clutch Plays 2025-2026 Season",
             "channel_name": "House of Highlights", "view_count": 3500000, "like_count": 55000,
             "comment_count": 2100, "published_at": "2026-05-20T00:00:00Z"},
        ],
        "default": [
            {"video_id": "fixture_def001", "title": "バスケットボール スーパープレー集",
             "channel_name": "Hoops Japan", "view_count": 300000, "like_count": 5000,
             "comment_count": 200, "published_at": "2026-05-10T00:00:00Z"},
        ],
    }
    matched = []
    for key, videos in fixtures.items():
        if key in query:
            matched.extend(videos)
    if not matched:
        matched = fixtures["default"]

    results = []
    for v in matched:
        results.append({
            "video_id": v["video_id"],
            "url": f"https://www.youtube.com/watch?v={v['video_id']}",
            "title": v["title"],
            "channel_name": v["channel_name"],
            "published_at": v["published_at"],
            "duration": None,
            "view_count": v["view_count"],
            "like_count": v["like_count"],
            "comment_count": v["comment_count"],
            "channel_subscriber_count": None,
            "thumbnail_url": None,
            "description": "",
            "search_query": query,
        })
    return results


def get_research_client(api_key=None):
    """利用可能なクライアントを返す（API優先、なければfixture）"""
    client = YouTubeResearchClient(api_key)
    if client.is_available:
        return client
    return FixtureResearchClient()
