import { prisma } from "@/lib/prisma";
import { NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const search = url.searchParams.get("search") || undefined;
    const videoType = url.searchParams.get("videoType") || undefined;
    const status = url.searchParams.get("status") || undefined;
    const outsourcerId = url.searchParams.get("outsourcerId") || undefined;
    const seriesName = url.searchParams.get("seriesName") || undefined;
    const theme = url.searchParams.get("theme") || undefined;

    const where: Record<string, unknown> = {};

    if (search) {
      where.OR = [
        { title: { contains: search } },
        { projectName: { contains: search } },
      ];
    }
    if (videoType) where.videoType = videoType;
    if (status) where.status = status;
    if (outsourcerId) where.outsourcerId = outsourcerId;
    if (seriesName) where.seriesName = seriesName;
    if (theme) where.theme = theme;

    const videos = await prisma.video.findMany({
      where,
      include: {
        outsourcer: true,
        metrics: true,
        shortsMetrics: true,
        quality: true,
        risks: true,
      },
      orderBy: { createdAt: "desc" },
    });

    return Response.json(videos);
  } catch (error) {
    console.error("GET /api/videos error:", error);
    return Response.json({ error: "動画一覧の取得に失敗しました" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const body = await request.json();

    const totalCost =
      (body.scriptCost || 0) +
      (body.editingCost || 0) +
      (body.shortsEditCost || 0) +
      (body.thumbnailCost || 0) +
      (body.materialCost || 0) +
      (body.bgmCost || 0) +
      (body.otherCost || 0);

    const video = await prisma.video.create({
      data: {
        projectName: body.projectName,
        title: body.title,
        videoType: body.videoType || "長尺",
        seriesName: body.seriesName,
        theme: body.theme,
        outsourcerId: body.outsourcerId,
        requestDate: body.requestDate ? new Date(body.requestDate) : undefined,
        firstDraftDue: body.firstDraftDue ? new Date(body.firstDraftDue) : undefined,
        deliveryDue: body.deliveryDue ? new Date(body.deliveryDue) : undefined,
        postDate: body.postDate ? new Date(body.postDate) : undefined,
        publicUrl: body.publicUrl,
        status: body.status || "企画中",
        scriptCost: body.scriptCost || 0,
        editingCost: body.editingCost || 0,
        shortsEditCost: body.shortsEditCost || 0,
        thumbnailCost: body.thumbnailCost || 0,
        materialCost: body.materialCost || 0,
        bgmCost: body.bgmCost || 0,
        otherCost: body.otherCost || 0,
        totalCost,
      },
      include: {
        outsourcer: true,
      },
    });

    return Response.json(video, { status: 201 });
  } catch (error) {
    console.error("POST /api/videos error:", error);
    return Response.json({ error: "動画の作成に失敗しました" }, { status: 500 });
  }
}
