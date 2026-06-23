import { prisma } from "@/lib/prisma";
import { NextRequest } from "next/server";
import { calcProfit, calcROI } from "@/lib/calculations";

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const monthParam = url.searchParams.get("month");

    // Parse YYYY-MM format, default to current month
    const now = new Date();
    let year = now.getFullYear();
    let month = now.getMonth() + 1;

    if (monthParam) {
      const parts = monthParam.split("-");
      if (parts.length === 2) {
        year = parseInt(parts[0], 10);
        month = parseInt(parts[1], 10);
      }
    }

    if (isNaN(year) || isNaN(month) || month < 1 || month > 12) {
      return Response.json(
        { error: "月の形式が不正です。YYYY-MM形式で指定してください" },
        { status: 400 }
      );
    }

    const startOfMonth = new Date(year, month - 1, 1);
    const endOfMonth = new Date(year, month, 0, 23, 59, 59);

    const monthlyVideos = await prisma.video.findMany({
      where: {
        postDate: { gte: startOfMonth, lte: endOfMonth },
      },
      include: {
        metrics: true,
        shortsMetrics: true,
        quality: true,
        risks: true,
        outsourcer: true,
      },
    });

    // Total calculations
    const totalVideos = monthlyVideos.length;
    const totalCost = monthlyVideos.reduce((s, v) => s + v.totalCost, 0);
    const totalRevenue = monthlyVideos.reduce(
      (s, v) => s + (v.metrics?.estimatedRevenue || 0),
      0
    );
    const totalProfit = calcProfit(totalRevenue, totalCost);
    const totalROI = calcROI(totalProfit, totalCost);

    // By type breakdown
    const longVideos = monthlyVideos.filter((v) => v.videoType === "長尺");
    const shortsVideos = monthlyVideos.filter((v) => v.videoType === "Shorts");

    const byType = {
      長尺: {
        count: longVideos.length,
        cost: longVideos.reduce((s, v) => s + v.totalCost, 0),
        revenue: longVideos.reduce(
          (s, v) => s + (v.metrics?.estimatedRevenue || 0),
          0
        ),
        profit: calcProfit(
          longVideos.reduce(
            (s, v) => s + (v.metrics?.estimatedRevenue || 0),
            0
          ),
          longVideos.reduce((s, v) => s + v.totalCost, 0)
        ),
      },
      Shorts: {
        count: shortsVideos.length,
        cost: shortsVideos.reduce((s, v) => s + v.totalCost, 0),
        revenue: shortsVideos.reduce(
          (s, v) => s + (v.metrics?.estimatedRevenue || 0),
          0
        ),
        profit: calcProfit(
          shortsVideos.reduce(
            (s, v) => s + (v.metrics?.estimatedRevenue || 0),
            0
          ),
          shortsVideos.reduce((s, v) => s + v.totalCost, 0)
        ),
      },
    };

    // Top 5 videos by revenue
    const top5ByRevenue = [...monthlyVideos]
      .sort(
        (a, b) =>
          (b.metrics?.estimatedRevenue || 0) -
          (a.metrics?.estimatedRevenue || 0)
      )
      .slice(0, 5)
      .map((v) => ({
        id: v.id,
        projectName: v.projectName,
        title: v.title,
        videoType: v.videoType,
        totalCost: v.totalCost,
        estimatedRevenue: Math.round(v.metrics?.estimatedRevenue || 0),
        profit: Math.round(
          calcProfit(v.metrics?.estimatedRevenue || 0, v.totalCost)
        ),
        totalViews: v.metrics?.totalViews || 0,
      }));

    // Cost breakdown by category
    const costBreakdown = {
      scriptCost: monthlyVideos.reduce((s, v) => s + v.scriptCost, 0),
      editingCost: monthlyVideos.reduce((s, v) => s + v.editingCost, 0),
      shortsEditCost: monthlyVideos.reduce((s, v) => s + v.shortsEditCost, 0),
      thumbnailCost: monthlyVideos.reduce((s, v) => s + v.thumbnailCost, 0),
      materialCost: monthlyVideos.reduce((s, v) => s + v.materialCost, 0),
      bgmCost: monthlyVideos.reduce((s, v) => s + v.bgmCost, 0),
      otherCost: monthlyVideos.reduce((s, v) => s + v.otherCost, 0),
    };

    // Average metrics
    const videosWithMetrics = monthlyVideos.filter((v) => v.metrics);
    const avgViews =
      videosWithMetrics.length > 0
        ? videosWithMetrics.reduce(
            (s, v) => s + (v.metrics?.totalViews || 0),
            0
          ) / videosWithMetrics.length
        : 0;
    const avgCTR =
      videosWithMetrics.length > 0
        ? videosWithMetrics.reduce((s, v) => s + (v.metrics?.ctr || 0), 0) /
          videosWithMetrics.length
        : 0;
    const avgRetention =
      videosWithMetrics.length > 0
        ? videosWithMetrics.reduce(
            (s, v) => s + (v.metrics?.avgRetention || 0),
            0
          ) / videosWithMetrics.length
        : 0;

    return Response.json({
      period: { year, month, label: `${year}-${String(month).padStart(2, "0")}` },
      summary: {
        totalVideos,
        totalCost,
        totalRevenue: Math.round(totalRevenue),
        totalProfit: Math.round(totalProfit),
        roi: Math.round(totalROI * 10) / 10,
      },
      byType,
      top5ByRevenue,
      costBreakdown,
      averageMetrics: {
        views: Math.round(avgViews),
        ctr: Math.round(avgCTR * 100) / 100,
        retention: Math.round(avgRetention * 100) / 100,
      },
    });
  } catch (error) {
    console.error("GET /api/reports error:", error);
    return Response.json(
      { error: "レポートの生成に失敗しました" },
      { status: 500 }
    );
  }
}
