import { prisma } from "@/lib/prisma";
import {
  calcProfit,
  calcROI,
  calcRecoveryRate,
  generateWarnings,
} from "@/lib/calculations";

export async function GET() {
  try {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    const endOfMonth = new Date(
      now.getFullYear(),
      now.getMonth() + 1,
      0,
      23,
      59,
      59
    );

    const allVideos = await prisma.video.findMany({
      include: {
        metrics: true,
        quality: true,
        risks: true,
        outsourcer: true,
        orders: true,
      },
    });

    // This month's posted videos
    const thisMonthVideos = allVideos.filter(
      (v) =>
        v.postDate &&
        new Date(v.postDate) >= startOfMonth &&
        new Date(v.postDate) <= endOfMonth
    );

    const thisMonthPostCount = thisMonthVideos.length;
    const thisMonthLongCount = thisMonthVideos.filter(
      (v) => v.videoType === "長尺"
    ).length;
    const thisMonthShortsCount = thisMonthVideos.filter(
      (v) => v.videoType === "Shorts"
    ).length;

    const thisMonthTotalCost = thisMonthVideos.reduce(
      (sum, v) => sum + v.totalCost,
      0
    );
    const thisMonthEstimatedRevenue = thisMonthVideos.reduce(
      (sum, v) => sum + (v.metrics?.estimatedRevenue || 0),
      0
    );
    const thisMonthProfit = calcProfit(
      thisMonthEstimatedRevenue,
      thisMonthTotalCost
    );

    // Unrecovered cost
    const unrecoveredCost = allVideos
      .filter(
        (v) =>
          v.status === "公開済み" &&
          v.totalCost > 0 &&
          (v.metrics?.estimatedRevenue || 0) < v.totalCost
      )
      .reduce(
        (sum, v) => sum + (v.totalCost - (v.metrics?.estimatedRevenue || 0)),
        0
      );

    // Production / revision counts
    const inProductionCount = allVideos.filter(
      (v) => v.status === "制作中" || v.status === "外注依頼済み"
    ).length;
    const inRevisionCount = allVideos.filter(
      (v) => v.status === "初稿確認中" || v.status === "修正中"
    ).length;

    // Overdue
    const overdueCount = allVideos.filter(
      (v) =>
        v.deliveryDue &&
        new Date(v.deliveryDue) < now &&
        v.status !== "公開済み" &&
        v.status !== "納品済み" &&
        v.status !== "中止"
    ).length;

    // Top profit / deficit videos
    const publishedVideos = allVideos
      .filter((v) => v.status === "公開済み" && v.metrics)
      .map((v) => {
        const revenue = v.metrics?.estimatedRevenue || 0;
        const profit = calcProfit(revenue, v.totalCost);
        const roi = calcROI(profit, v.totalCost);
        const recoveryRate = calcRecoveryRate(revenue, v.totalCost);
        return {
          id: v.id,
          projectName: v.projectName,
          title: v.title,
          videoType: v.videoType,
          totalCost: v.totalCost,
          estimatedRevenue: Math.round(revenue),
          profit: Math.round(profit),
          roi: Math.round(roi * 10) / 10,
          recoveryRate: Math.round(recoveryRate * 10) / 10,
          totalViews: v.metrics?.totalViews || 0,
        };
      });

    const topProfitVideos = [...publishedVideos]
      .sort((a, b) => b.profit - a.profit)
      .slice(0, 5);

    const deficitVideos = [...publishedVideos]
      .filter((v) => v.profit < 0)
      .sort((a, b) => a.profit - b.profit)
      .slice(0, 5);

    // Warnings
    const warnings: Array<{
      videoId: string;
      projectName: string;
      warnings: string[];
    }> = [];
    for (const v of allVideos) {
      const maxRiskLevel =
        v.risks.length > 0
          ? v.risks.reduce((max, r) => {
              const levels = ["低", "中", "高", "公開不可"];
              return levels.indexOf(r.riskLevel) > levels.indexOf(max)
                ? r.riskLevel
                : max;
            }, "低")
          : undefined;

      const unpaidOrders = v.orders.filter(
        (o) => o.paymentStatus === "未払い"
      );

      const videoWarnings = generateWarnings({
        status: v.status,
        deliveryDue: v.deliveryDue?.toISOString() || null,
        totalCost: v.totalCost,
        estimatedRevenue: v.metrics?.estimatedRevenue || undefined,
        riskLevel: maxRiskLevel,
        paymentStatus: unpaidOrders.length > 0 ? "未払い" : "支払済み",
        revisionCount: v.quality?.firstDraftRevisions || 0,
      });

      if (videoWarnings.length > 0) {
        warnings.push({
          videoId: v.id,
          projectName: v.projectName,
          warnings: videoWarnings,
        });
      }
    }

    return Response.json({
      thisMonth: {
        postCount: thisMonthPostCount,
        longCount: thisMonthLongCount,
        shortsCount: thisMonthShortsCount,
        totalCost: thisMonthTotalCost,
        estimatedRevenue: Math.round(thisMonthEstimatedRevenue),
        profit: Math.round(thisMonthProfit),
      },
      unrecoveredCost: Math.round(unrecoveredCost),
      inProductionCount,
      inRevisionCount,
      overdueCount,
      topProfitVideos,
      deficitVideos,
      warnings,
      totalVideoCount: allVideos.length,
    });
  } catch (error) {
    console.error("GET /api/dashboard error:", error);
    return Response.json(
      { error: "ダッシュボードデータの取得に失敗しました" },
      { status: 500 }
    );
  }
}
