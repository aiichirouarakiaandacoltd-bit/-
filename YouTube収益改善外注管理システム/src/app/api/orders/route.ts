import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const orders = await prisma.order.findMany({
      include: {
        video: true,
        outsourcer: true,
      },
      orderBy: { createdAt: "desc" },
    });

    return Response.json(orders);
  } catch (error) {
    console.error("GET /api/orders error:", error);
    return Response.json({ error: "発注一覧の取得に失敗しました" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const order = await prisma.order.create({
      data: {
        videoId: body.videoId,
        outsourcerId: body.outsourcerId,
        description: body.description,
        deliverable: body.deliverable,
        price: body.price,
        deadline: body.deadline ? new Date(body.deadline) : undefined,
        instructionUrl: body.instructionUrl,
        referenceUrl: body.referenceUrl,
        bgmUrl: body.bgmUrl,
        startDate: body.startDate ? new Date(body.startDate) : undefined,
        firstDraftDue: body.firstDraftDue ? new Date(body.firstDraftDue) : undefined,
        revisionDate: body.revisionDate ? new Date(body.revisionDate) : undefined,
        deliveryDate: body.deliveryDate ? new Date(body.deliveryDate) : undefined,
        paymentStatus: body.paymentStatus || "未払い",
        reviewStatus: body.reviewStatus || "未検収",
      },
      include: {
        video: true,
        outsourcer: true,
      },
    });

    return Response.json(order, { status: 201 });
  } catch (error) {
    console.error("POST /api/orders error:", error);
    return Response.json({ error: "発注の作成に失敗しました" }, { status: 500 });
  }
}
