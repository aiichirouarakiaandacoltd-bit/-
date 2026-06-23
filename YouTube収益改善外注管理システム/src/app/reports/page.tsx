"use client";

import { useEffect, useState } from "react";

interface ReportData {
  period: { year: number; month: number; label: string };
  summary: {
    totalVideos: number;
    totalCost: number;
    totalRevenue: number;
    totalProfit: number;
    roi: number;
  };
  byType: Record<
    string,
    { count: number; cost: number; revenue: number; profit: number }
  >;
  top5ByRevenue: {
    id: string;
    projectName: string;
    title: string | null;
    videoType: string;
    totalCost: number;
    estimatedRevenue: number;
    profit: number;
    totalViews: number;
  }[];
  costBreakdown: Record<string, number>;
  averageMetrics: { views: number; ctr: number; retention: number };
}

const COST_LABELS: Record<string, string> = {
  scriptCost: "台本費",
  editingCost: "編集費",
  shortsEditCost: "Shorts編集費",
  thumbnailCost: "サムネイル費",
  materialCost: "素材費",
  bgmCost: "BGM費",
  otherCost: "その他",
};

export default function ReportsPage() {
  const now = new Date();
  const defaultMonth = `${now.getFullYear()}-${String(
    now.getMonth() + 1
  ).padStart(2, "0")}`;

  const [month, setMonth] = useState(defaultMonth);
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`/api/reports?month=${month}`)
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [month]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">月次レポート</h1>
        <input
          type="month"
          value={month}
          onChange={(e) => setMonth(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-500 text-lg">読み込み中...</p>
        </div>
      ) : !data ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-red-500 text-lg">データの取得に失敗しました</p>
        </div>
      ) : (
        <>
          {/* Overview */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">概要</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-500">動画数</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.summary.totalVideos}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">制作費</p>
                <p className="text-2xl font-bold text-gray-900">
                  ¥{data.summary.totalCost.toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">収益</p>
                <p className="text-2xl font-bold text-blue-600">
                  ¥{data.summary.totalRevenue.toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">利益</p>
                <p
                  className={`text-2xl font-bold ${
                    data.summary.totalProfit >= 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  ¥{data.summary.totalProfit.toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">ROI</p>
                <p className="text-2xl font-bold text-gray-900">
                  {data.summary.roi}%
                </p>
              </div>
            </div>
          </div>

          {/* Type Breakdown */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                種別内訳
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      種別
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      本数
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      制作費
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      収益
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      利益
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(data.byType).map(([type, stats]) => (
                    <tr key={type}>
                      <td className="px-6 py-3 text-sm font-medium text-gray-900">
                        {type}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-500 text-right">
                        {stats.count}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-500 text-right">
                        ¥{stats.cost.toLocaleString()}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-500 text-right">
                        ¥{Math.round(stats.revenue).toLocaleString()}
                      </td>
                      <td
                        className={`px-6 py-3 text-sm text-right font-medium ${
                          stats.profit >= 0
                            ? "text-green-600"
                            : "text-red-600"
                        }`}
                      >
                        ¥{Math.round(stats.profit).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Top Videos */}
          {data.top5ByRevenue.length > 0 && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">
                  収益トップ動画
                </h2>
              </div>
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
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        再生数
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        制作費
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        収益
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        利益
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {data.top5ByRevenue.map((v) => (
                      <tr key={v.id}>
                        <td className="px-6 py-3 text-sm text-gray-900">
                          {v.title || v.projectName}
                        </td>
                        <td className="px-6 py-3 text-sm text-gray-500">
                          {v.videoType}
                        </td>
                        <td className="px-6 py-3 text-sm text-gray-500 text-right">
                          {v.totalViews.toLocaleString()}
                        </td>
                        <td className="px-6 py-3 text-sm text-gray-500 text-right">
                          ¥{v.totalCost.toLocaleString()}
                        </td>
                        <td className="px-6 py-3 text-sm text-gray-500 text-right">
                          ¥{v.estimatedRevenue.toLocaleString()}
                        </td>
                        <td
                          className={`px-6 py-3 text-sm text-right font-medium ${
                            v.profit >= 0
                              ? "text-green-600"
                              : "text-red-600"
                          }`}
                        >
                          ¥{v.profit.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Cost Breakdown */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">費用内訳</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                      項目
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                      金額
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(data.costBreakdown).map(([key, value]) => (
                    <tr key={key}>
                      <td className="px-6 py-3 text-sm text-gray-900">
                        {COST_LABELS[key] || key}
                      </td>
                      <td className="px-6 py-3 text-sm text-gray-500 text-right">
                        ¥{value.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Average Metrics */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              平均指標
            </h2>
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <p className="text-sm text-gray-500">平均再生数</p>
                <p className="text-xl font-bold text-gray-900">
                  {data.averageMetrics.views.toLocaleString()}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">平均CTR</p>
                <p className="text-xl font-bold text-gray-900">
                  {data.averageMetrics.ctr}%
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-500">平均維持率</p>
                <p className="text-xl font-bold text-gray-900">
                  {data.averageMetrics.retention}%
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
