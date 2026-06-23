import { prisma } from "@/lib/prisma";
import { NextRequest } from "next/server";
import { calcProfit } from "@/lib/calculations";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type VideoWithMetrics = any;

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const months = parseInt(url.searchParams.get("months") || "12", 10);

    const videos: VideoWithMetrics[] = await prisma.video.findMany({
      where: { status: "公開済み" },
      include: { metrics: true },
      orderBy: { postDate: "asc" },
    });

    // Monthly revenue/cost/profit breakdown
    const monthlyData: Record<
      string,
      { month: string; revenue: number; cost: number; profit: number; count: number }
    > = {};

    const now = new Date();
    for (let i = months - 1; i >= 0; i--) {
      const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
      monthlyData[key] = { month: key, revenue: 0, cost: 0, profit: 0, count: 0 };
    }

    for (const video of videos) {
      if (!video.postDate) continue;
      const pd = new Date(video.postDate);
      const key = `${pd.getFullYear()}-${String(pd.getMonth() + 1).padStart(2, "0")}`;
      if (monthlyData[key]) {
        const revenue = video.metrics?.estimatedRevenue || 0;
        monthlyData[key].revenue += revenue;
        monthlyData[key].cost += video.totalCost;
        monthlyData[key].profit += calcProfit(revenue, video.totalCost);
        monthlyData[key].count += 1;
      }
    }

    const monthlyTrend = Object.values(monthlyData).map((d) => ({
      ...d,
      revenue: Math.round(d.revenue),
      profit: Math.round(d.profit),
    }));

    // Video type comparison
    const longVideos = videos.filter((v: VideoWithMetrics) => v.videoType === "長尺");
    const shortsVideos = videos.filter((v: VideoWithMetrics) => v.videoType === "Shorts");

    const calcTypeStats = (vids: VideoWithMetrics[]) => {
      const totalCost = vids.reduce((s: number, v: VideoWithMetrics) => s + v.totalCost, 0);
      const totalRevenue = vids.reduce(
        (s: number, v: VideoWithMetrics) => s + (v.metrics?.estimatedRevenue || 0),
        0
      );
      const totalViews = vids.reduce(
        (s: number, v: VideoWithMetrics) => s + (v.metrics?.totalViews || 0),
        0
      );
      const avgCtr =
        vids.length > 0
          ? vids.reduce((s: number, v: VideoWithMetrics) => s + (v.metrics?.ctr || 0), 0) / vids.length
          : 0;
      const avgRetention =
        vids.length > 0
          ? vids.reduce((s: number, v: VideoWithMetrics) => s + (v.metrics?.avgRetention || 0), 0) /
            vids.length
          : 0;

      return {
        count: vids.length,
        totalCost,
        totalRevenue: Math.round(totalRevenue),
        totalProfit: Math.round(calcProfit(totalRevenue, totalCost)),
        totalViews,
        avgCtr: Math.round(avgCtr * 100) / 100,
        avgRetention: Math.round(avgRetention * 100) / 100,
        avgCostPerVideo:
          vids.length > 0 ? Math.round(totalCost / vids.length) : 0,
      };
    };

    const videoTypeComparison = {
      長尺: calcTypeStats(longVideos),
      Shorts: calcTypeStats(shortsVideos),
    };

    // Cost breakdown
    const totalScriptCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.scriptCost, 0);
    const totalEditingCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.editingCost, 0);
    const totalShortsEditCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.shortsEditCost, 0);
    const totalThumbnailCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.thumbnailCost, 0);
    const totalMaterialCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.materialCost, 0);
    const totalBgmCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.bgmCost, 0);
    const totalOtherCost = videos.reduce((s: number, v: VideoWithMetrics) => s + v.otherCost, 0);

    const costBreakdown = {
      台本: totalScriptCost,
      編集: totalEditingCost,
      Shorts編集: totalShortsEditCost,
      サムネイル: totalThumbnailCost,
      素材: totalMaterialCost,
      BGM: totalBgmCost,
      その他: totalOtherCost,
    };

    return Response.json({
      monthlyTrend,
      videoTypeComparison,
      costBreakdown,
    });
  } catch (error) {
    console.error("GET /api/analytics error:", error);
    return Response.json({ error: "分析データの取得に失敗しました" }, { status: 500 });
  }
}
