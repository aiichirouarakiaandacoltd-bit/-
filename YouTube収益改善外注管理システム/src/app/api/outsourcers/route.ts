import { prisma } from "@/lib/prisma";

export async function GET() {
  try {
    const outsourcers = await prisma.outsourcer.findMany({
      include: {
        _count: {
          select: { videos: true, orders: true },
        },
      },
      orderBy: { createdAt: "desc" },
    });

    return Response.json(outsourcers);
  } catch (error) {
    console.error("GET /api/outsourcers error:", error);
    return Response.json({ error: "外注先一覧の取得に失敗しました" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const outsourcer = await prisma.outsourcer.create({
      data: {
        name: body.name,
        serviceName: body.serviceName,
        contact: body.contact,
        availableTasks: body.availableTasks,
        longVideoPrice: body.longVideoPrice,
        shortsPrice: body.shortsPrice,
        thumbnailPrice: body.thumbnailPrice,
        deliveryDays: body.deliveryDays,
        software: body.software,
        voicevoxCapable: body.voicevoxCapable ?? false,
        materialCapable: body.materialCapable ?? false,
        thumbnailCapable: body.thumbnailCapable ?? false,
        continuationOk: body.continuationOk ?? true,
        continuationStatus: body.continuationStatus || "テスト継続",
        notes: body.notes,
      },
    });

    return Response.json(outsourcer, { status: 201 });
  } catch (error) {
    console.error("POST /api/outsourcers error:", error);
    return Response.json({ error: "外注先の作成に失敗しました" }, { status: 500 });
  }
}
