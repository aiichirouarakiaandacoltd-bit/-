"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import StatCard from "@/components/StatCard";
import WarningBanner from "@/components/WarningBanner";

interface DashboardData {
  thisMonth: {
    postCount: number;
    longCount: number;
    shortsCount: number;
    totalCost: number;
    estimatedRevenue: number;
    profit: number;
  };
  unrecoveredCost: number;
  inProductionCount: number;
  inRevisionCount: number;
  overdueCount: number;
  topProfitVideos: {
    id: string;
    projectName: string;
    title: string | null;
    videoType: string;
    totalCost: number;
    estimatedRevenue: number;
    profit: number;
    roi: number;
    recoveryRate: number;
    totalViews: number;
  }[];
  deficitVideos: {
    id: string;
    projectName: string;
    title: string | null;
    videoType: string;
    totalCost: number;
    estimatedRevenue: number;
    profit: number;
    roi: number;
    recoveryRate: number;
    totalViews: number;
  }[];
  warnings: {
    videoId: string;
    projectName: string;
    warnings: string[];
  }[];
  totalVideoCount: number;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/dashboard")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch");
        return res.json();
      })
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500 text-lg">読み込み中...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-500 text-lg">データの取得に失敗しました</p>
      </div>
    );
  }

  const {
    thisMonth,
    unrecoveredCost,
    inProductionCount,
    inRevisionCount,
    overdueCount,
    topProfitVideos,
    deficitVideos,
    warnings,
    totalVideoCount,
  } = data;

  // Build monthly chart from top profit videos (simplified - use analytics for full chart)
  const warningsForBanner = warnings.map((w) => ({
    videoId: w.videoId,
    title: w.projectName,
    messages: w.warnings,
  }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">ダッシュボード</h1>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        <StatCard
          title="総動画数"
          value={totalVideoCount}
          color="blue"
        />
        <StatCard
          title="今月の投稿"
          value={thisMonth.postCount}
          subtitle={`長尺: ${thisMonth.longCount} / Shorts: ${thisMonth.shortsCount}`}
          color="blue"
        />
        <StatCard
          title="今月の制作費"
          value={`¥${thisMonth.totalCost.toLocaleString()}`}
          color="gray"
        />
        <StatCard
          title="今月の推定収益"
          value={`¥${thisMonth.estimatedRevenue.toLocaleString()}`}
          color="blue"
        />
        <StatCard
          title="今月の利益"
          value={`¥${thisMonth.profit.toLocaleString()}`}
          color={thisMonth.profit >= 0 ? "green" : "red"}
        />
        <StatCard
          title="未回収費"
          value={`¥${unrecoveredCost.toLocaleString()}`}
          color={unrecoveredCost > 0 ? "red" : "gray"}
        />
        <StatCard
          title="制作中"
          value={inProductionCount}
          color="blue"
        />
        <StatCard
          title="修正中"
          value={inRevisionCount}
          color="yellow"
        />
        <StatCard
          title="納期遅延"
          value={overdueCount}
          color={overdueCount > 0 ? "red" : "green"}
        />
      </div>

      {/* Warnings */}
      {warningsForBanner.length > 0 && <WarningBanner warnings={warningsForBanner} />}

      {/* Top Profit Videos */}
      {topProfitVideos.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">
              利益トップ動画
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">
                    タイトル
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">
                    種別
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    再生数
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    制作費
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    収益
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    利益
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    ROI
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {topProfitVideos.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <Link
                        href={`/videos/${v.id}`}
                        className="text-blue-600 hover:underline"
                      >
                        {v.title || v.projectName}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {v.videoType}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      {v.totalViews.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      ¥{v.totalCost.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      ¥{v.estimatedRevenue.toLocaleString()}
                    </td>
                    <td
                      className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${
                        v.profit >= 0 ? "text-green-600" : "text-red-600"
                      }`}
                    >
                      ¥{v.profit.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      {v.roi.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Deficit Videos */}
      {deficitVideos.length > 0 && (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-red-600">赤字動画</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">
                    タイトル
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500">
                    種別
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    制作費
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    収益
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    利益
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500">
                    ROI
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {deficitVideos.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <Link
                        href={`/videos/${v.id}`}
                        className="text-blue-600 hover:underline"
                      >
                        {v.title || v.projectName}
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {v.videoType}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      ¥{v.totalCost.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      ¥{v.estimatedRevenue.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-red-600">
                      ¥{v.profit.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">
                      {v.roi.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
