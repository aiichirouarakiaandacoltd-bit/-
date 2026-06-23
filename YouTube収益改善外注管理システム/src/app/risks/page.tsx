"use client";

import { useEffect, useState } from "react";

interface VideoRisk {
  id: string;
  riskLevel: string;
  notes: string | null;
  aiGeneratedRoyal: boolean;
  faceModification: boolean;
  unknownRightsPhoto: boolean;
  tvFootage: boolean;
  longNewsFootage: boolean;
  otherChannelReuse: boolean;
  watermarkedMaterial: boolean;
  unknownSourceMaterial: boolean;
  reuseContentRisk: boolean;
  exaggeration: boolean;
  innerThoughtClaim: boolean;
  politicalClaim: boolean;
  adSuitabilityRisk: boolean;
}

interface Video {
  id: string;
  projectName: string;
  title: string | null;
  videoType: string;
  risks: VideoRisk[];
}

const RISK_FIELD_LABELS: Record<string, string> = {
  aiGeneratedRoyal: "AI生成素材",
  faceModification: "顔加工",
  unknownRightsPhoto: "権利不明写真",
  tvFootage: "TV映像",
  longNewsFootage: "ニュース映像(長時間)",
  otherChannelReuse: "他チャンネル流用",
  watermarkedMaterial: "ウォーターマーク素材",
  unknownSourceMaterial: "出典不明素材",
  reuseContentRisk: "リユースコンテンツリスク",
  exaggeration: "誇張表現",
  innerThoughtClaim: "心情断定",
  politicalClaim: "政治的主張",
  adSuitabilityRisk: "広告適合性リスク",
};

const RISK_LEVEL_COLORS: Record<string, string> = {
  低: "bg-green-100 text-green-800",
  中: "bg-yellow-100 text-yellow-800",
  高: "bg-orange-100 text-orange-800",
  公開不可: "bg-red-100 text-red-800",
};

const RISK_LEVELS = ["低", "中", "高", "公開不可"];

export default function RisksPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterLevel, setFilterLevel] = useState<string>("all");

  useEffect(() => {
    fetch("/api/videos")
      .then((res) => res.json())
      .then((data) => {
        setVideos(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500 text-lg">読み込み中...</p>
      </div>
    );
  }

  // Filter videos with risks
  const videosWithRisks = videos.filter(
    (v) => v.risks && v.risks.length > 0
  );

  // Flatten to risk entries with video info
  const riskEntries = videosWithRisks.flatMap((video) =>
    video.risks.map((risk) => ({
      video,
      risk,
    }))
  );

  // Apply filter
  const filtered =
    filterLevel === "all"
      ? riskEntries
      : riskEntries.filter((entry) => entry.risk.riskLevel === filterLevel);

  function getActiveRiskLabels(risk: VideoRisk): string[] {
    const labels: string[] = [];
    for (const [field, label] of Object.entries(RISK_FIELD_LABELS)) {
      if (risk[field as keyof VideoRisk] === true) {
        labels.push(label);
      }
    }
    return labels;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">リスク管理</h1>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">リスクレベル:</label>
          <select
            value={filterLevel}
            onChange={(e) => setFilterLevel(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="all">すべて</option>
            {RISK_LEVELS.map((level) => (
              <option key={level} value={level}>
                {level}
              </option>
            ))}
          </select>
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center">
          <p className="text-gray-500">リスクのある動画はありません</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    タイトル
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    種別
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    リスクレベル
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    リスク内容
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    メモ
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filtered.map((entry, idx) => {
                  const riskLabels = getActiveRiskLabels(entry.risk);
                  const levelColor =
                    RISK_LEVEL_COLORS[entry.risk.riskLevel] ||
                    "bg-gray-100 text-gray-700";
                  return (
                    <tr key={`${entry.video.id}-${idx}`}>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {entry.video.title || entry.video.projectName}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {entry.video.videoType}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span
                          className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${levelColor}`}
                        >
                          {entry.risk.riskLevel}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-700">
                        {riskLabels.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {riskLabels.map((label) => (
                              <span
                                key={label}
                                className="inline-block bg-gray-100 text-gray-700 rounded px-2 py-0.5 text-xs"
                              >
                                {label}
                              </span>
                            ))}
                          </div>
                        ) : (
                          "-"
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {entry.risk.notes || "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
