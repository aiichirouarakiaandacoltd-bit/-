import { prisma } from "@/lib/prisma";

export async function POST() {
  try {
    // Delete existing data in reverse dependency order
    await prisma.videoRisk.deleteMany();
    await prisma.videoQuality.deleteMany();
    await prisma.videoShortsMetrics.deleteMany();
    await prisma.videoMetrics.deleteMany();
    await prisma.order.deleteMany();
    await prisma.video.deleteMany();
    await prisma.outsourcer.deleteMany();

    // Create outsourcers with specified names and prices
    const kawaguchi = await prisma.outsourcer.create({
      data: {
        name: "川口祐太",
        serviceName: "ココナラ",
        contact: "kawaguchi@example.com",
        availableTasks: "Shorts編集",
        shortsPrice: 3000,
        deliveryDays: 5,
        software: "Premiere Pro",
        voicevoxCapable: true,
        materialCapable: false,
        thumbnailCapable: false,
        continuationOk: true,
        continuationStatus: "継続中",
      },
    });

    const elcy = await prisma.outsourcer.create({
      data: {
        name: "エルシー",
        serviceName: "ランサーズ",
        contact: "elcy@example.com",
        availableTasks: "長尺編集,サムネイル作成",
        longVideoPrice: 7000,
        thumbnailPrice: 1500,
        deliveryDays: 7,
        software: "Premiere Pro, Photoshop",
        voicevoxCapable: true,
        materialCapable: true,
        thumbnailCapable: true,
        continuationOk: true,
        continuationStatus: "継続中",
      },
    });

    const tanaka = await prisma.outsourcer.create({
      data: {
        name: "前進主義 田中",
        serviceName: "ココナラ",
        contact: "tanaka@example.com",
        availableTasks: "Shorts編集",
        shortsPrice: 1500,
        deliveryDays: 3,
        software: "DaVinci Resolve",
        voicevoxCapable: true,
        materialCapable: false,
        thumbnailCapable: false,
        continuationOk: true,
        continuationStatus: "テスト継続",
      },
    });

    const ren = await prisma.outsourcer.create({
      data: {
        name: "漣レン",
        serviceName: "クラウドワークス",
        contact: "ren@example.com",
        availableTasks: "長尺編集,サムネイル作成",
        longVideoPrice: 4000,
        thumbnailPrice: 1000,
        deliveryDays: 5,
        software: "Premiere Pro, Canva",
        voicevoxCapable: false,
        materialCapable: true,
        thumbnailCapable: true,
        continuationOk: true,
        continuationStatus: "継続中",
      },
    });

    const now = new Date();
    const daysAgo = (d: number) => new Date(now.getTime() - d * 86400000);

    // Video 1: Published long video - high performer
    const video1 = await prisma.video.create({
      data: {
        projectName: "【驚愕】70代が知らない年金の真実",
        title: "【驚愕】70代が知らない年金の真実トップ5",
        videoType: "長尺",
        seriesName: "年金シリーズ",
        theme: "年金・社会保障",
        outsourcerId: elcy.id,
        requestDate: daysAgo(30),
        firstDraftDue: daysAgo(23),
        deliveryDue: daysAgo(20),
        postDate: daysAgo(15),
        status: "公開済み",
        scriptCost: 0,
        editingCost: 7000,
        thumbnailCost: 1500,
        totalCost: 8500,
      },
    });

    await prisma.videoMetrics.create({
      data: {
        videoId: video1.id,
        views24h: 8500,
        views48h: 15000,
        views7d: 45000,
        views30d: 78000,
        totalViews: 78000,
        impressions: 250000,
        ctr: 8.2,
        avgWatchTime: 6.5,
        avgRetention: 42,
        likes: 850,
        comments: 120,
        subscribersGained: 45,
        estimatedRevenue: 23400,
        rpm: 300,
      },
    });

    await prisma.videoQuality.create({
      data: {
        videoId: video1.id,
        firstDraftRevisions: 1,
        majorRevisions: 0,
        minorRevisions: 1,
        reviewTime: 30,
        finalScore: 85,
      },
    });

    // Video 2: Published Shorts - moderate performance
    const video2 = await prisma.video.create({
      data: {
        projectName: "60秒でわかる高血圧対策",
        title: "60秒でわかる高血圧対策 #shorts",
        videoType: "Shorts",
        seriesName: "60秒健康シリーズ",
        theme: "健康",
        outsourcerId: kawaguchi.id,
        requestDate: daysAgo(20),
        firstDraftDue: daysAgo(15),
        deliveryDue: daysAgo(13),
        postDate: daysAgo(10),
        status: "公開済み",
        shortsEditCost: 3000,
        totalCost: 3000,
      },
    });

    await prisma.videoMetrics.create({
      data: {
        videoId: video2.id,
        views24h: 12000,
        views48h: 25000,
        views7d: 85000,
        views30d: 120000,
        totalViews: 120000,
        impressions: 500000,
        ctr: 5.5,
        avgWatchTime: 0.8,
        avgRetention: 75,
        likes: 2500,
        comments: 45,
        subscribersGained: 80,
        estimatedRevenue: 3600,
        rpm: 30,
      },
    });

    await prisma.videoShortsMetrics.create({
      data: {
        videoId: video2.id,
        feedImpressions: 500000,
        selectRate: 12.5,
        swipeAwayRate: 25,
        avgPlayRate: 85,
        hasLoopViews: true,
      },
    });

    // Video 3: In production - long video
    const video3 = await prisma.video.create({
      data: {
        projectName: "【完全版】定年後の資産運用ガイド",
        videoType: "長尺",
        seriesName: "資産運用シリーズ",
        theme: "投資・資産運用",
        outsourcerId: ren.id,
        requestDate: daysAgo(5),
        firstDraftDue: daysAgo(-2),
        deliveryDue: daysAgo(-5),
        status: "制作中",
        editingCost: 4000,
        thumbnailCost: 1000,
        totalCost: 5000,
      },
    });

    // Video 4: Published but deficit
    const video4 = await prisma.video.create({
      data: {
        projectName: "知っておきたい相続の基本",
        title: "知っておきたい相続の基本｜初心者向け解説",
        videoType: "長尺",
        theme: "相続・法律",
        outsourcerId: elcy.id,
        requestDate: daysAgo(45),
        firstDraftDue: daysAgo(38),
        deliveryDue: daysAgo(35),
        postDate: daysAgo(30),
        status: "公開済み",
        editingCost: 7000,
        thumbnailCost: 1500,
        totalCost: 8500,
      },
    });

    await prisma.videoMetrics.create({
      data: {
        videoId: video4.id,
        views24h: 1200,
        views48h: 2500,
        views7d: 5500,
        views30d: 8000,
        totalViews: 8000,
        impressions: 80000,
        ctr: 3.2,
        avgWatchTime: 4.0,
        avgRetention: 28,
        likes: 120,
        comments: 8,
        subscribersGained: 5,
        estimatedRevenue: 2400,
        rpm: 300,
      },
    });

    await prisma.videoQuality.create({
      data: {
        videoId: video4.id,
        firstDraftRevisions: 3,
        majorRevisions: 1,
        minorRevisions: 2,
        typoErrors: 2,
        reviewTime: 90,
        finalScore: 55,
      },
    });

    await prisma.videoRisk.create({
      data: {
        videoId: video4.id,
        unknownRightsPhoto: true,
        riskLevel: "中",
        notes: "一部写真の出典不明",
      },
    });

    // Video 5: Shorts in revision
    const video5 = await prisma.video.create({
      data: {
        projectName: "膝の痛みを和らげるストレッチ",
        title: "膝の痛みを和らげるストレッチ #shorts",
        videoType: "Shorts",
        theme: "健康",
        outsourcerId: tanaka.id,
        requestDate: daysAgo(7),
        firstDraftDue: daysAgo(4),
        deliveryDue: daysAgo(-1),
        status: "修正中",
        shortsEditCost: 1500,
        totalCost: 1500,
      },
    });

    await prisma.videoQuality.create({
      data: {
        videoId: video5.id,
        firstDraftRevisions: 2,
        majorRevisions: 1,
        voiceMisreads: 1,
        reviewTime: 45,
      },
    });

    // Video 6: Planning stage
    await prisma.video.create({
      data: {
        projectName: "【保存版】介護保険の賢い使い方",
        videoType: "長尺",
        seriesName: "介護シリーズ",
        theme: "介護",
        status: "企画中",
      },
    });

    // Create sample orders
    await prisma.order.create({
      data: {
        videoId: video1.id,
        outsourcerId: elcy.id,
        description: "長尺動画編集（年金の真実）",
        deliverable: "編集済み動画ファイル + サムネイル",
        price: 8500,
        startDate: daysAgo(30),
        firstDraftDue: daysAgo(23),
        deliveryDate: daysAgo(20),
        paymentStatus: "支払済み",
        reviewStatus: "検収済み",
      },
    });

    await prisma.order.create({
      data: {
        videoId: video2.id,
        outsourcerId: kawaguchi.id,
        description: "Shorts編集（高血圧対策）",
        deliverable: "Shorts動画ファイル",
        price: 3000,
        startDate: daysAgo(20),
        firstDraftDue: daysAgo(15),
        deliveryDate: daysAgo(13),
        paymentStatus: "支払済み",
        reviewStatus: "検収済み",
      },
    });

    await prisma.order.create({
      data: {
        videoId: video3.id,
        outsourcerId: ren.id,
        description: "長尺動画編集（資産運用ガイド）",
        deliverable: "編集済み動画ファイル + サムネイル",
        price: 5000,
        startDate: daysAgo(5),
        firstDraftDue: daysAgo(-2),
        deadline: daysAgo(-5),
        paymentStatus: "未払い",
        reviewStatus: "未検収",
      },
    });

    await prisma.order.create({
      data: {
        videoId: video4.id,
        outsourcerId: elcy.id,
        description: "長尺動画編集（相続の基本）",
        deliverable: "編集済み動画ファイル + サムネイル",
        price: 8500,
        startDate: daysAgo(45),
        firstDraftDue: daysAgo(38),
        deliveryDate: daysAgo(35),
        paymentStatus: "支払済み",
        reviewStatus: "検収済み",
      },
    });

    await prisma.order.create({
      data: {
        videoId: video5.id,
        outsourcerId: tanaka.id,
        description: "Shorts編集（膝ストレッチ）",
        deliverable: "Shorts動画ファイル",
        price: 1500,
        startDate: daysAgo(7),
        firstDraftDue: daysAgo(4),
        deadline: daysAgo(-1),
        paymentStatus: "未払い",
        reviewStatus: "未検収",
      },
    });

    return Response.json({
      success: true,
      message: "サンプルデータを作成しました",
      counts: {
        outsourcers: 4,
        videos: 6,
        metrics: 3,
        shortsMetrics: 1,
        quality: 3,
        risks: 1,
        orders: 5,
      },
    });
  } catch (error) {
    console.error("POST /api/seed error:", error);
    return Response.json(
      { error: "シードデータの作成に失敗しました" },
      { status: 500 }
    );
  }
}
