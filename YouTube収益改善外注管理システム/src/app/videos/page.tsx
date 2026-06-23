'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import StatusBadge from '@/components/StatusBadge';
import { calcProfit, calcROI } from '@/lib/calculations';

interface Video {
  id: string;
  projectName: string;
  title: string | null;
  videoType: string;
  status: string;
  totalCost: number;
  outsourcer: { id: string; name: string } | null;
  metrics: { estimatedRevenue: number | null } | null;
}

const VIDEO_TYPES = ['長尺', 'Shorts'] as const;
const STATUSES = ['企画中', '台本作成中', '制作中', '修正中', '納品済み', '公開済み', '非公開'] as const;

export default function VideosPage() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [videoType, setVideoType] = useState('');
  const [status, setStatus] = useState('');

  const fetchVideos = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (videoType) params.set('videoType', videoType);
      if (status) params.set('status', status);
      const res = await fetch(`/api/videos?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setVideos(data);
      }
    } catch (err) {
      console.error('Failed to fetch videos:', err);
    } finally {
      setLoading(false);
    }
  }, [search, videoType, status]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchVideos();
    }, 300);
    return () => clearTimeout(timer);
  }, [fetchVideos]);

  return (
    <div className="lg:ml-64">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">動画一覧</h1>
        <Link
          href="/videos/new"
          className="inline-flex items-center rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          新規作成
        </Link>
      </div>

      <div className="mb-6 flex flex-wrap gap-4">
        <input
          type="text"
          placeholder="タイトル・企画名で検索..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        />
        <select
          value={videoType}
          onChange={(e) => setVideoType(e.target.value)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">種別: すべて</option>
          {VIDEO_TYPES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">ステータス: すべて</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-gray-500">読み込み中...</div>
        </div>
      ) : videos.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">動画が見つかりません</p>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">タイトル</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">種別</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">外注者名</th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">ステータス</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">制作費</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">推定収益</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">利益</th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">ROI</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {videos.map((video) => {
                const revenue = video.metrics?.estimatedRevenue ?? 0;
                const profit = calcProfit(revenue, video.totalCost);
                const roi = calcROI(profit, video.totalCost);

                return (
                  <tr key={video.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-sm">
                      <Link href={`/videos/${video.id}`} className="font-medium text-blue-600 hover:text-blue-800 hover:underline">
                        {video.title || video.projectName}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">{video.videoType}</td>
                    <td className="px-4 py-3 text-sm text-gray-700">{video.outsourcer?.name ?? '---'}</td>
                    <td className="px-4 py-3 text-sm">
                      <StatusBadge status={video.status} />
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ¥{video.totalCost.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-right text-gray-700">
                      ¥{revenue.toLocaleString()}
                    </td>
                    <td className={`px-4 py-3 text-sm text-right font-medium ${profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ¥{profit.toLocaleString()}
                    </td>
                    <td className={`px-4 py-3 text-sm text-right font-medium ${roi >= 100 ? 'text-green-600' : roi >= 0 ? 'text-gray-700' : 'text-red-600'}`}>
                      {video.totalCost > 0 ? `${roi.toFixed(1)}%` : '---'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
