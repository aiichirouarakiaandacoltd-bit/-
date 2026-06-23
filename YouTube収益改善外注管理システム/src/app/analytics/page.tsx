"use client";

import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface MonthlyTrend {
  month: string;
  revenue: number;
  cost: number;
  profit: number;
  count: number;
}

interface TypeStats {
  count: number;
  totalCost: number;
  totalRevenue: number;
  totalProfit: number;
  totalViews: number;
  avgCtr: number;
  avgRetention: number;
  avgCostPerVideo: number;
}

interface AnalyticsData {
  monthlyTrend: MonthlyTrend[];
  videoTypeComparison: Record<string, TypeStats>;
  costBreakdown: Record<string, number>;
}

const PIE_COLORS = [
  "#2563eb",
  "#ef4444",
  "#22c55e",
  "#f59e0b",
  "#8b5cf6",
  "#ec4899",
  "#6b7280",
];

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/analytics")
      .then((res) => res.json())
      .then((json) => {
        setData(json);
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

  if (!data) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-red-500 text-lg">データの取得に失敗しました</p>
      </div>
    );
  }

  const { monthlyTrend, videoTypeComparison, costBreakdown } = data;

  // Prepare type comparison bar chart data
  const typeComparisonData = Object.entries(videoTypeComparison).map(
    ([type, stats]) => ({
      type,
      本数: stats.count,
      制作費: stats.totalCost,
      収益: stats.totalRevenue,
      利益: stats.totalProfit,
    })
  );

  // Prepare pie chart data
  const pieData = Object.entries(costBreakdown)
    .filter(([, value]) => value > 0)
    .map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">分析</h1>

      {/* Monthly Trend */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          月別収益/費用/利益
        </h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={monthlyTrend}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip
              formatter={(value) => `¥${Number(value).toLocaleString()}`}
            />
            <Legend />
            <Bar dataKey="revenue" name="収益" fill="#2563eb" />
            <Bar dataKey="cost" name="制作費" fill="#ef4444" />
            <Bar dataKey="profit" name="利益" fill="#22c55e" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Video Type Comparison */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          長尺 vs Shorts比較
        </h2>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={typeComparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="type" />
            <YAxis />
            <Tooltip
              formatter={(value, name) =>
                name === "本数"
                  ? `${value}本`
                  : `¥${Number(value).toLocaleString()}`
              }
            />
            <Legend />
            <Bar dataKey="制作費" fill="#ef4444" />
            <Bar dataKey="収益" fill="#2563eb" />
            <Bar dataKey="利益" fill="#22c55e" />
          </BarChart>
        </ResponsiveContainer>

        {/* Type summary table */}
        <div className="mt-6 overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                  種別
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  本数
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  制作費合計
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  収益合計
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  利益合計
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  平均単価
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  平均CTR
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                  平均維持率
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {Object.entries(videoTypeComparison).map(([type, stats]) => (
                <tr key={type}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {type}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">
                    {stats.count}本
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">
                    ¥{stats.totalCost.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">
                    ¥{stats.totalRevenue.toLocaleString()}
                  </td>
                  <td
                    className={`px-4 py-3 text-sm text-right font-medium ${
                      stats.totalProfit >= 0
                        ? "text-green-600"
                        : "text-red-600"
                    }`}
                  >
                    ¥{stats.totalProfit.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">
                    ¥{stats.avgCostPerVideo.toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">
                    {stats.avgCtr}%
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">
                    {stats.avgRetention}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Cost Breakdown Pie */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">費用内訳</h2>
        {pieData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine
                label={({ name, percent }) =>
                  `${name} ${((percent ?? 0) * 100).toFixed(0)}%`
                }
                outerRadius={140}
                dataKey="value"
              >
                {pieData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={PIE_COLORS[index % PIE_COLORS.length]}
                  />
                ))}
              </Pie>
              <Tooltip
                formatter={(value) => `¥${Number(value).toLocaleString()}`}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-gray-500">データがありません</p>
        )}
      </div>
    </div>
  );
}
