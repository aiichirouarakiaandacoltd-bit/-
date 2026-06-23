import { prisma } from "@/lib/prisma";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const video = await prisma.video.findUnique({
      where: { id },
      include: {
        outsourcer: true,
        metrics: true,
        shortsMetrics: true,
        quality: true,
        risks: true,
        orders: {
          include: { outsourcer: true },
        },
      },
    });

    if (!video) {
      return Response.json({ error: "動画が見つかりません" }, { status: 404 });
    }

    return Response.json(video);
  } catch (error) {
    console.error("GET /api/videos/[id] error:", error);
    return Response.json({ error: "動画の取得に失敗しました" }, { status: 500 });
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    const totalCost =
      (body.scriptCost ?? undefined) !== undefined ||
      (body.editingCost ?? undefined) !== undefined
        ? (body.scriptCost || 0) +
          (body.editingCost || 0) +
          (body.shortsEditCost || 0) +
          (body.thumbnailCost || 0) +
          (body.materialCost || 0) +
          (body.bgmCost || 0) +
          (body.otherCost || 0)
        : undefined;

    const data: Record<string, unknown> = { ...body };
    if (totalCost !== undefined) data.totalCost = totalCost;

    // Convert date strings to Date objects
    for (const field of ["requestDate", "firstDraftDue", "deliveryDue", "postDate"]) {
      if (data[field] && typeof data[field] === "string") {
        data[field] = new Date(data[field] as string);
      }
    }

    // Remove relation fields that shouldn't be in data
    delete data.outsourcer;
    delete data.metrics;
    delete data.shortsMetrics;
    delete data.quality;
    delete data.risks;
    delete data.orders;

    const video = await prisma.video.update({
      where: { id },
      data,
      include: {
        outsourcer: true,
        metrics: true,
        shortsMetrics: true,
        quality: true,
        risks: true,
      },
    });

    return Response.json(video);
  } catch (error) {
    console.error("PUT /api/videos/[id] error:", error);
    return Response.json({ error: "動画の更新に失敗しました" }, { status: 500 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    await prisma.video.delete({ where: { id } });

    return Response.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/videos/[id] error:", error);
    return Response.json({ error: "動画の削除に失敗しました" }, { status: 500 });
  }
}
