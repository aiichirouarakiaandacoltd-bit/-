import { prisma } from "@/lib/prisma";
import {
  calcProfit,
  calcROI,
  calcRecoveryRate,
} from "@/lib/calculations";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const outsourcer = await prisma.outsourcer.findUnique({
      where: { id },
      include: {
        videos: {
          include: {
            metrics: true,
            quality: true,
          },
        },
        orders: true,
      },
    });

    if (!outsourcer) {
      return Response.json({ error: "外注先が見つかりません" }, { status: 404 });
    }

    // Calculate stats
    const totalCost = outsourcer.videos.reduce((sum, v) => sum + v.totalCost, 0);
    const totalRevenue = outsourcer.videos.reduce(
      (sum, v) => sum + (v.metrics?.estimatedRevenue || 0),
      0
    );
    const profit = calcProfit(totalRevenue, totalCost);
    const roi = calcROI(profit, totalCost);
    const recoveryRate = calcRecoveryRate(totalRevenue, totalCost);
    const videoCount = outsourcer.videos.length;
    const completedCount = outsourcer.videos.filter(
      (v) => v.status === "公開済み" || v.status === "納品済み"
    ).length;

    const avgRevisionCount =
      outsourcer.videos.length > 0
        ? outsourcer.videos.reduce(
            (sum, v) => sum + (v.quality?.firstDraftRevisions || 0),
            0
          ) / outsourcer.videos.length
        : 0;

    const stats = {
      totalCost,
      totalRevenue,
      profit,
      roi,
      recoveryRate,
      videoCount,
      completedCount,
      avgRevisionCount: Math.round(avgRevisionCount * 10) / 10,
      orderCount: outsourcer.orders.length,
      totalOrderAmount: outsourcer.orders.reduce((sum, o) => sum + o.price, 0),
    };

    return Response.json({ ...outsourcer, stats });
  } catch (error) {
    console.error("GET /api/outsourcers/[id] error:", error);
    return Response.json({ error: "外注先の取得に失敗しました" }, { status: 500 });
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    // Remove relation fields
    delete body.videos;
    delete body.orders;
    delete body._count;
    delete body.stats;

    const outsourcer = await prisma.outsourcer.update({
      where: { id },
      data: body,
    });

    return Response.json(outsourcer);
  } catch (error) {
    console.error("PUT /api/outsourcers/[id] error:", error);
    return Response.json({ error: "外注先の更新に失敗しました" }, { status: 500 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    await prisma.outsourcer.delete({ where: { id } });

    return Response.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/outsourcers/[id] error:", error);
    return Response.json({ error: "外注先の削除に失敗しました" }, { status: 500 });
  }
}
