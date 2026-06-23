'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

type Outsourcer = {
  id: string;
  name: string;
  availableTasks: string | null;
  longVideoPrice: number;
  shortsPrice: number;
  continuationStatus: string;
  _count: {
    videos: number;
    orders: number;
  };
};

const statusColor: Record<string, string> = {
  '継続OK': 'bg-green-100 text-green-800',
  'テスト継続': 'bg-yellow-100 text-yellow-800',
  '要検討': 'bg-orange-100 text-orange-800',
  '停止': 'bg-red-100 text-red-800',
};

function formatPrice(value: number): string {
  return `¥${value.toLocaleString()}`;
}

export default function OutsourcersPage() {
  const [outsourcers, setOutsourcers] = useState<Outsourcer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/outsourcers')
      .then((res) => {
        if (!res.ok) throw new Error('取得に失敗しました');
        return res.json();
      })
      .then((data) => setOutsourcers(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">外注先一覧</h1>
        <Link
          href="/outsourcers/new"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
        >
          新規登録
        </Link>
      </div>

      <div className="overflow-x-auto bg-white shadow rounded-lg">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                氏名
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                担当業務
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                長尺単価
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Shorts単価
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                依頼本数
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                継続判定
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {outsourcers.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                  外注先が登録されていません
                </td>
              </tr>
            ) : (
              outsourcers.map((o) => (
                <tr key={o.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      href={`/outsourcers/${o.id}`}
                      className="text-blue-600 hover:text-blue-800 hover:underline font-medium"
                    >
                      {o.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                    {o.availableTasks || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                    {formatPrice(o.longVideoPrice)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                    {formatPrice(o.shortsPrice)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                    {o._count.videos}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColor[o.continuationStatus] || 'bg-gray-100 text-gray-800'}`}
                    >
                      {o.continuationStatus}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
