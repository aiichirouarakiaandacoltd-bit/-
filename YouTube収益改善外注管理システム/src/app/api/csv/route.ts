import { prisma } from "@/lib/prisma";
import { NextRequest } from "next/server";

function escapeCsvField(value: unknown): string {
  if (value === null || value === undefined) return "";
  const str = String(value);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function toCsvRow(fields: unknown[]): string {
  return fields.map(escapeCsvField).join(",");
}

function parseCsvLine(line: string): string[] {
  const result: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    if (inQuotes) {
      if (line[i] === '"' && line[i + 1] === '"') {
        current += '"';
        i++;
      } else if (line[i] === '"') {
        inQuotes = false;
      } else {
        current += line[i];
      }
    } else {
      if (line[i] === '"') {
        inQuotes = true;
      } else if (line[i] === ",") {
        result.push(current.trim());
        current = "";
      } else {
        current += line[i];
      }
    }
  }
  result.push(current.trim());
  return result;
}

export async function GET(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const type = url.searchParams.get("type") || "videos";

    if (type === "videos") {
      const videos = await prisma.video.findMany({
        include: {
          outsourcer: true,
          metrics: true,
        },
        orderBy: { createdAt: "desc" },
      });

      const headers = [
        "ID",
        "企画名",
        "タイトル",
        "動画種別",
        "シリーズ名",
        "テーマ",
        "外注先",
        "ステータス",
        "依頼日",
        "初稿期限",
        "納品期限",
        "投稿日",
        "台本費",
        "編集費",
        "Shorts編集費",
        "サムネイル費",
        "素材費",
        "BGM費",
        "その他費用",
        "合計費用",
        "推定収益",
        "総再生数",
        "CTR",
        "平均維持率",
      ];

      const rows = videos.map((v) =>
        toCsvRow([
          v.id,
          v.projectName,
          v.title,
          v.videoType,
          v.seriesName,
          v.theme,
          v.outsourcer?.name,
          v.status,
          v.requestDate?.toISOString().split("T")[0],
          v.firstDraftDue?.toISOString().split("T")[0],
          v.deliveryDue?.toISOString().split("T")[0],
          v.postDate?.toISOString().split("T")[0],
          v.scriptCost,
          v.editingCost,
          v.shortsEditCost,
          v.thumbnailCost,
          v.materialCost,
          v.bgmCost,
          v.otherCost,
          v.totalCost,
          v.metrics?.estimatedRevenue,
          v.metrics?.totalViews,
          v.metrics?.ctr,
          v.metrics?.avgRetention,
        ])
      );

      const csv = [toCsvRow(headers), ...rows].join("\n");

      return new Response(csv, {
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": `attachment; filename="videos_${new Date().toISOString().split("T")[0]}.csv"`,
        },
      });
    }

    if (type === "outsourcers") {
      const outsourcers = await prisma.outsourcer.findMany({
        orderBy: { createdAt: "desc" },
      });

      const headers = [
        "ID",
        "名前",
        "サービス名",
        "連絡先",
        "対応業務",
        "長尺価格",
        "Shorts価格",
        "サムネイル価格",
        "納品日数",
        "使用ソフト",
        "VOICEVOX対応",
        "素材調達可",
        "サムネイル対応",
        "継続OK",
        "継続状況",
        "備考",
      ];

      const rows = outsourcers.map((o) =>
        toCsvRow([
          o.id,
          o.name,
          o.serviceName,
          o.contact,
          o.availableTasks,
          o.longVideoPrice,
          o.shortsPrice,
          o.thumbnailPrice,
          o.deliveryDays,
          o.software,
          o.voicevoxCapable ? "はい" : "いいえ",
          o.materialCapable ? "はい" : "いいえ",
          o.thumbnailCapable ? "はい" : "いいえ",
          o.continuationOk ? "はい" : "いいえ",
          o.continuationStatus,
          o.notes,
        ])
      );

      const csv = [toCsvRow(headers), ...rows].join("\n");

      return new Response(csv, {
        headers: {
          "Content-Type": "text/csv; charset=utf-8",
          "Content-Disposition": `attachment; filename="outsourcers_${new Date().toISOString().split("T")[0]}.csv"`,
        },
      });
    }

    return Response.json(
      { error: "未対応のタイプです。videos または outsourcers を指定してください" },
      { status: 400 }
    );
  } catch (error) {
    console.error("GET /api/csv error:", error);
    return Response.json(
      { error: "CSVエクスポートに失敗しました" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const type = (formData.get("type") as string) || "videos";

    if (!file) {
      return Response.json(
        { error: "ファイルが指定されていません" },
        { status: 400 }
      );
    }

    const text = await file.text();
    const lines = text.split("\n").filter((line) => line.trim());

    if (lines.length < 2) {
      return Response.json(
        { error: "CSVデータが不足しています" },
        { status: 400 }
      );
    }

    const headers = parseCsvLine(lines[0]);
    const dataRows = lines.slice(1).map(parseCsvLine);

    let importedCount = 0;

    if (type === "videos") {
      for (const row of dataRows) {
        const getVal = (headerName: string) => {
          const idx = headers.indexOf(headerName);
          return idx >= 0 ? row[idx] || "" : "";
        };

        const id = getVal("ID") || undefined;
        const data = {
          projectName: getVal("企画名") || "未設定",
          title: getVal("タイトル") || undefined,
          videoType: getVal("動画種別") || "長尺",
          seriesName: getVal("シリーズ名") || undefined,
          theme: getVal("テーマ") || undefined,
          status: getVal("ステータス") || "企画中",
          scriptCost: parseInt(getVal("台本費")) || 0,
          editingCost: parseInt(getVal("編集費")) || 0,
          shortsEditCost: parseInt(getVal("Shorts編集費")) || 0,
          thumbnailCost: parseInt(getVal("サムネイル費")) || 0,
          materialCost: parseInt(getVal("素材費")) || 0,
          bgmCost: parseInt(getVal("BGM費")) || 0,
          otherCost: parseInt(getVal("その他費用")) || 0,
          totalCost: parseInt(getVal("合計費用")) || 0,
          requestDate: getVal("依頼日")
            ? new Date(getVal("依頼日"))
            : undefined,
          firstDraftDue: getVal("初稿期限")
            ? new Date(getVal("初稿期限"))
            : undefined,
          deliveryDue: getVal("納品期限")
            ? new Date(getVal("納品期限"))
            : undefined,
          postDate: getVal("投稿日")
            ? new Date(getVal("投稿日"))
            : undefined,
        };

        if (id) {
          await prisma.video.upsert({
            where: { id },
            update: data,
            create: { id, ...data },
          });
        } else {
          await prisma.video.create({ data });
        }
        importedCount++;
      }
    } else if (type === "outsourcers") {
      for (const row of dataRows) {
        const getVal = (headerName: string) => {
          const idx = headers.indexOf(headerName);
          return idx >= 0 ? row[idx] || "" : "";
        };

        const id = getVal("ID") || undefined;
        const data = {
          name: getVal("名前") || "未設定",
          serviceName: getVal("サービス名") || undefined,
          contact: getVal("連絡先") || undefined,
          availableTasks: getVal("対応業務") || undefined,
          longVideoPrice: parseInt(getVal("長尺価格")) || undefined,
          shortsPrice: parseInt(getVal("Shorts価格")) || undefined,
          thumbnailPrice: parseInt(getVal("サムネイル価格")) || undefined,
          deliveryDays: parseInt(getVal("納品日数")) || undefined,
          software: getVal("使用ソフト") || undefined,
          voicevoxCapable: getVal("VOICEVOX対応") === "はい",
          materialCapable: getVal("素材調達可") === "はい",
          thumbnailCapable: getVal("サムネイル対応") === "はい",
          continuationOk: getVal("継続OK") !== "いいえ",
          continuationStatus: getVal("継続状況") || "テスト継続",
          notes: getVal("備考") || undefined,
        };

        if (id) {
          await prisma.outsourcer.upsert({
            where: { id },
            update: data,
            create: { id, ...data },
          });
        } else {
          await prisma.outsourcer.create({ data });
        }
        importedCount++;
      }
    } else {
      return Response.json(
        { error: "未対応のタイプです。videos または outsourcers を指定してください" },
        { status: 400 }
      );
    }

    return Response.json({
      success: true,
      importedCount,
      message: `${importedCount}件のデータをインポートしました`,
    });
  } catch (error) {
    console.error("POST /api/csv error:", error);
    return Response.json(
      { error: "CSVインポートに失敗しました" },
      { status: 500 }
    );
  }
}
