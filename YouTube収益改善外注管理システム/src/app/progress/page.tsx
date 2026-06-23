"use client";

import { useEffect, useState } from "react";
import { format, differenceInDays } from "date-fns";
import StatusBadge from "@/components/StatusBadge";

interface Video {
  id: string;
  projectName: string;
  title: string | null;
  videoType: string;
  status: string;
  deliveryDue: string | null;
  outsourcer: { id: string; name: string } | null;
}

const STATUS_ORDER = [
  "企画中",
  "台本作成中",
  "制作中",
  "修正中",
  "納品済み",
  "公開済み",
];

export default function ProgressPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);

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

  const grouped: Record<string, Video[]> = {};
  for (const status of STATUS_ORDER) {
    grouped[status] = [];
  }
  for (const video of videos) {
    if (grouped[video.status]) {
      grouped[video.status].push(video);
    } else {
      // Unknown statuses go into their own group
      if (!grouped[video.status]) grouped[video.status] = [];
      grouped[video.status].push(video);
    }
  }

  const now = new Date();

  function isOverdue(video: Video): boolean {
    if (!video.deliveryDue) return false;
    if (video.status === "公開済み" || video.status === "納品済み") return false;
    return new Date(video.deliveryDue) < now;
  }

  function daysUntilDeadline(deliveryDue: string | null): string {
    if (!deliveryDue) return "-";
    const days = differenceInDays(new Date(deliveryDue), now);
    if (days < 0) return `${Math.abs(days)}日超過`;
    if (days === 0) return "本日";
    return `あと${days}日`;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">制作進捗</h1>

      {STATUS_ORDER.map((status) => {
        const items = grouped[status];
        if (!items || items.length === 0) return null;

        return (
          <div key={status} className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-3">
              <StatusBadge status={status} />
              <span className="text-sm text-gray-500">{items.length}件</span>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      タイトル
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      外注先
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      納品期限
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      残り日数
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {items.map((video) => {
                    const overdue = isOverdue(video);
                    return (
                      <tr
                        key={video.id}
                        className={overdue ? "bg-red-50" : ""}
                      >
                        <td
                          className={`px-6 py-4 whitespace-nowrap text-sm ${
                            overdue
                              ? "text-red-700 font-semibold"
                              : "text-gray-900"
                          }`}
                        >
                          {video.title || video.projectName}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {video.outsourcer?.name || "-"}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {video.deliveryDue
                            ? format(new Date(video.deliveryDue), "yyyy/MM/dd")
                            : "-"}
                        </td>
                        <td
                          className={`px-6 py-4 whitespace-nowrap text-sm font-medium ${
                            overdue ? "text-red-600" : "text-gray-700"
                          }`}
                        >
                          {daysUntilDeadline(video.deliveryDue)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}
    </div>
  );
}
