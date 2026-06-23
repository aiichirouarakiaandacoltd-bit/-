import { prisma } from "@/lib/prisma";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const order = await prisma.order.findUnique({
      where: { id },
      include: {
        video: true,
        outsourcer: true,
      },
    });

    if (!order) {
      return Response.json({ error: "発注が見つかりません" }, { status: 404 });
    }

    return Response.json(order);
  } catch (error) {
    console.error("GET /api/orders/[id] error:", error);
    return Response.json({ error: "発注の取得に失敗しました" }, { status: 500 });
  }
}

export async function PUT(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();

    // Convert date strings to Date objects
    const dateFields = [
      "deadline",
      "startDate",
      "firstDraftDue",
      "revisionDate",
      "deliveryDate",
    ];
    for (const field of dateFields) {
      if (body[field] && typeof body[field] === "string") {
        body[field] = new Date(body[field]);
      }
    }

    // Remove relation fields
    delete body.video;
    delete body.outsourcer;

    const order = await prisma.order.update({
      where: { id },
      data: body,
      include: {
        video: true,
        outsourcer: true,
      },
    });

    return Response.json(order);
  } catch (error) {
    console.error("PUT /api/orders/[id] error:", error);
    return Response.json({ error: "発注の更新に失敗しました" }, { status: 500 });
  }
}

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    await prisma.order.delete({ where: { id } });

    return Response.json({ success: true });
  } catch (error) {
    console.error("DELETE /api/orders/[id] error:", error);
    return Response.json({ error: "発注の削除に失敗しました" }, { status: 500 });
  }
}
