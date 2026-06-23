'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

type Video = {
  id: string;
  title: string;
  status: string;
  totalCost: number;
  metrics?: {
    estimatedRevenue: number;
  } | null;
};

type Order = {
  id: string;
  description: string | null;
  deliverable: string | null;
  price: number;
  paymentStatus: string;
  reviewStatus: string | null;
};

type Stats = {
  totalCost: number;
  totalRevenue: number;
  profit: number;
  roi: number;
  recoveryRate: number;
  videoCount: number;
  completedCount: number;
  avgRevisionCount: number;
  orderCount: number;
  totalOrderAmount: number;
};

type OutsourcerDetail = {
  id: string;
  name: string;
  serviceName: string | null;
  contact: string | null;
  availableTasks: string | null;
  longVideoPrice: number;
  shortsPrice: number;
  thumbnailPrice: number;
  deliveryDays: number | null;
  software: string | null;
  voicevoxCapable: boolean;
  materialCapable: boolean;
  thumbnailCapable: boolean;
  continuationOk: boolean;
  continuationStatus: string;
  notes: string | null;
  videos: Video[];
  orders: Order[];
  stats: Stats;
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

export default function OutsourcerDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [outsourcer, setOutsourcer] = useState<OutsourcerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;
    fetch(`/api/outsourcers/${params.id}`)
      .then((res) => {
        if (!res.ok) throw new Error('外注先の取得に失敗しました');
        return res.json();
      })
      .then((data) => setOutsourcer(data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [params.id]);

  const handleDelete = async () => {
    if (!confirm('この外注先を削除してもよろしいですか？')) return;
    try {
      const res = await fetch(`/api/outsourcers/${params.id}`, {
        method: 'DELETE',
      });
      if (!res.ok) throw new Error('削除に失敗しました');
      router.push('/outsourcers');
    } catch (err) {
      alert(err instanceof Error ? err.message : '削除に失敗しました');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">読み込み中...</p>
      </div>
    );
  }

  if (error || !outsourcer) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500">{error || '外注先が見つかりません'}</p>
      </div>
    );
  }

  const { stats } = outsourcer;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <Link
            href="/outsourcers"
            className="text-sm text-blue-600 hover:underline"
          >
            &larr; 外注先一覧に戻る
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 mt-1">
            {outsourcer.name}
          </h1>
        </div>
        <div className="flex gap-3">
          <Link
            href={`/outsourcers/${outsourcer.id}/edit`}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 transition-colors"
          >
            編集
          </Link>
          <button
            onClick={handleDelete}
            className="inline-flex items-center px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-md hover:bg-red-700 transition-colors"
          >
            削除
          </button>
        </div>
      </div>

      {/* Outsourcer Info */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">基本情報</h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">氏名</dt>
            <dd className="mt-1 text-sm text-gray-900">{outsourcer.name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">サービス名</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {outsourcer.serviceName || '-'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">連絡先</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {outsourcer.contact || '-'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">担当業務</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {outsourcer.availableTasks || '-'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">長尺単価</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {formatPrice(outsourcer.longVideoPrice)}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Shorts単価</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {formatPrice(outsourcer.shortsPrice)}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">
              サムネイル単価
            </dt>
            <dd className="mt-1 text-sm text-gray-900">
              {formatPrice(outsourcer.thumbnailPrice)}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">納期(日)</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {outsourcer.deliveryDays ?? '-'}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">使用ソフト</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {outsourcer.software || '-'}
            </dd>
          </div>
          <div className="sm:col-span-2 lg:col-span-3">
            <dt className="text-sm font-medium text-gray-500 mb-2">
              対応可能
            </dt>
            <dd className="flex flex-wrap gap-2">
              {outsourcer.voicevoxCapable && (
                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                  VOICEVOX対応
                </span>
              )}
              {outsourcer.materialCapable && (
                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-indigo-100 text-indigo-800">
                  素材提供対応
                </span>
              )}
              {outsourcer.thumbnailCapable && (
                <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-teal-100 text-teal-800">
                  サムネイル対応
                </span>
              )}
              {!outsourcer.voicevoxCapable &&
                !outsourcer.materialCapable &&
                !outsourcer.thumbnailCapable && (
                  <span className="text-sm text-gray-400">なし</span>
                )}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">継続判定</dt>
            <dd className="mt-1">
              <span
                className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${statusColor[outsourcer.continuationStatus] || 'bg-gray-100 text-gray-800'}`}
              >
                {outsourcer.continuationStatus}
              </span>
            </dd>
          </div>
          {outsourcer.notes && (
            <div className="sm:col-span-2 lg:col-span-3">
              <dt className="text-sm font-medium text-gray-500">備考</dt>
              <dd className="mt-1 text-sm text-gray-900 whitespace-pre-wrap">
                {outsourcer.notes}
              </dd>
            </div>
          )}
        </dl>
      </div>

      {/* Stats */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          パフォーマンス統計
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">総コスト</p>
            <p className="text-lg font-bold text-gray-900">
              {formatPrice(stats.totalCost)}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">総収益</p>
            <p className="text-lg font-bold text-gray-900">
              {formatPrice(stats.totalRevenue)}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">利益</p>
            <p
              className={`text-lg font-bold ${stats.profit >= 0 ? 'text-green-700' : 'text-red-700'}`}
            >
              {formatPrice(stats.profit)}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">ROI</p>
            <p className="text-lg font-bold text-gray-900">
              {stats.roi.toFixed(1)}%
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">回収率</p>
            <p className="text-lg font-bold text-gray-900">
              {stats.recoveryRate.toFixed(1)}%
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">動画数</p>
            <p className="text-lg font-bold text-gray-900">
              {stats.videoCount}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">完了数</p>
            <p className="text-lg font-bold text-gray-900">
              {stats.completedCount}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">平均修正回数</p>
            <p className="text-lg font-bold text-gray-900">
              {stats.avgRevisionCount}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">発注数</p>
            <p className="text-lg font-bold text-gray-900">
              {stats.orderCount}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-500">発注総額</p>
            <p className="text-lg font-bold text-gray-900">
              {formatPrice(stats.totalOrderAmount)}
            </p>
          </div>
        </div>
      </div>

      {/* Videos Table */}
      <div className="bg-white shadow rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          担当動画一覧
        </h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  タイトル
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ステータス
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  コスト
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  収益
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {outsourcer.videos.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-6 py-4 text-center text-gray-500"
                  >
                    担当動画はありません
                  </td>
                </tr>
              ) : (
                outsourcer.videos.map((v) => (
                  <tr key={v.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {v.title}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {v.status}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                      {formatPrice(v.totalCost)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                      {formatPrice(v.metrics?.estimatedRevenue || 0)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">発注履歴</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  説明
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  成果物
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  金額
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  支払状況
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  レビュー状況
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {outsourcer.orders.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="px-6 py-4 text-center text-gray-500"
                  >
                    発注履歴はありません
                  </td>
                </tr>
              ) : (
                outsourcer.orders.map((o) => (
                  <tr key={o.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {o.description || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {o.deliverable || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 text-right">
                      {formatPrice(o.price)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {o.paymentStatus}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">
                      {o.reviewStatus || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
