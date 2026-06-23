'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import StatusBadge from '@/components/StatusBadge';
import {
  calcProfit,
  calcROI,
  calcRecoveryStatus,
  calcVideoScore,
  calcRevisionBurdenScore,
  generateWarnings,
  analyzeGrowthFactors,
  generateImprovementSuggestions,
} from '@/lib/calculations';

interface VideoData {
  id: string;
  projectName: string;
  title: string | null;
  videoType: string;
  seriesName: string | null;
  theme: string | null;
  status: string;
  outsourcerId: string | null;
  outsourcer: { id: string; name: string } | null;
  requestDate: string | null;
  firstDraftDue: string | null;
  deliveryDue: string | null;
  postDate: string | null;
  publicUrl: string | null;
  scriptCost: number;
  editingCost: number;
  shortsEditCost: number;
  thumbnailCost: number;
  materialCost: number;
  bgmCost: number;
  otherCost: number;
  totalCost: number;
  createdAt: string;
  updatedAt: string;
  metrics: {
    views24h: number | null;
    views48h: number | null;
    views7d: number | null;
    views30d: number | null;
    totalViews: number | null;
    impressions: number | null;
    ctr: number | null;
    avgWatchTime: number | null;
    avgRetention: number | null;
    likes: number | null;
    comments: number | null;
    subscribersGained: number | null;
    estimatedRevenue: number | null;
    rpm: number | null;
  } | null;
  quality: {
    firstDraftRevisions: number;
    majorRevisions: number;
    minorRevisions: number;
    typoErrors: number;
    voiceMisreads: number;
    subtitleMismatch: number;
    materialMismatch: number;
    reviewTime: number | null;
    finalScore: number | null;
  } | null;
  risks: Array<{
    id: string;
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
    riskLevel: string;
    notes: string | null;
  }>;
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '---';
  return new Date(dateStr).toLocaleDateString('ja-JP');
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex border-b border-gray-100 py-2">
      <dt className="w-40 shrink-0 text-sm font-medium text-gray-500">{label}</dt>
      <dd className="text-sm text-gray-900">{value ?? '---'}</dd>
    </div>
  );
}

export default function VideoDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [video, setVideo] = useState<VideoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    async function fetchVideo() {
      try {
        const res = await fetch(`/api/videos/${id}`);
        if (res.ok) {
          setVideo(await res.json());
        }
      } catch (err) {
        console.error('Failed to fetch video:', err);
      } finally {
        setLoading(false);
      }
    }
    if (id) fetchVideo();
  }, [id]);

  async function handleDelete() {
    if (!confirm('この動画を削除しますか？この操作は元に戻せません。')) return;
    setDeleting(true);
    try {
      const res = await fetch(`/api/videos/${id}`, { method: 'DELETE' });
      if (res.ok) {
        router.push('/videos');
      } else {
        alert('削除に失敗しました');
      }
    } catch {
      alert('削除に失敗しました');
    } finally {
      setDeleting(false);
    }
  }

  if (loading) {
    return (
      <div className="lg:ml-64 flex items-center justify-center py-12">
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  if (!video) {
    return (
      <div className="lg:ml-64">
        <p className="text-gray-500">動画が見つかりません</p>
        <Link href="/videos" className="text-blue-600 hover:underline mt-4 inline-block">一覧に戻る</Link>
      </div>
    );
  }

  const revenue = video.metrics?.estimatedRevenue ?? 0;
  const profit = calcProfit(revenue, video.totalCost);
  const roi = calcROI(profit, video.totalCost);
  const recoveryStatus = calcRecoveryStatus(revenue, video.totalCost);

  const totalRevisions = (video.quality?.firstDraftRevisions ?? 0) + (video.quality?.majorRevisions ?? 0) + (video.quality?.minorRevisions ?? 0);
  const revisionBurden = calcRevisionBurdenScore(
    totalRevisions,
    video.quality?.majorRevisions ?? 0,
    video.quality?.reviewTime ?? 0
  );

  const riskBooleanFields = [
    'aiGeneratedRoyal', 'faceModification', 'unknownRightsPhoto', 'tvFootage',
    'longNewsFootage', 'otherChannelReuse', 'watermarkedMaterial', 'unknownSourceMaterial',
    'reuseContentRisk', 'exaggeration', 'innerThoughtClaim', 'politicalClaim', 'adSuitabilityRisk',
  ] as const;
  const riskCount = video.risks.reduce((acc, risk) => {
    return acc + riskBooleanFields.filter((f) => risk[f]).length;
  }, 0);

  const videoScore = calcVideoScore({
    totalViews: video.metrics?.totalViews ?? undefined,
    ctr: video.metrics?.ctr ?? undefined,
    avgRetention: video.metrics?.avgRetention ?? undefined,
    profit,
    roi,
    subscribersGained: video.metrics?.subscribersGained ?? undefined,
    comments: video.metrics?.comments ?? undefined,
    views30d: video.metrics?.views30d ?? undefined,
    totalCost: video.totalCost,
    revisionBurden,
    riskCount,
  });

  const warnings = generateWarnings({
    status: video.status,
    deliveryDue: video.deliveryDue,
    totalCost: video.totalCost,
    estimatedRevenue: revenue,
    riskLevel: video.risks[0]?.riskLevel,
    revisionCount: totalRevisions,
  });

  const growthFactors = analyzeGrowthFactors({
    ctr: video.metrics?.ctr ?? undefined,
    avgRetention: video.metrics?.avgRetention ?? undefined,
    views24h: video.metrics?.views24h ?? undefined,
    totalViews: video.metrics?.totalViews ?? undefined,
    subscribersGained: video.metrics?.subscribersGained ?? undefined,
    comments: video.metrics?.comments ?? undefined,
  });

  const suggestions = generateImprovementSuggestions({
    ctr: video.metrics?.ctr ?? undefined,
    avgRetention: video.metrics?.avgRetention ?? undefined,
    totalViews: video.metrics?.totalViews ?? undefined,
    estimatedRevenue: revenue,
    totalCost: video.totalCost,
  });

  const riskLabels: Record<string, string> = {
    aiGeneratedRoyal: 'AI生成ロイヤリティ',
    faceModification: '顔加工',
    unknownRightsPhoto: '権利不明写真',
    tvFootage: 'テレビ映像',
    longNewsFootage: '長尺ニュース映像',
    otherChannelReuse: '他チャンネル素材再利用',
    watermarkedMaterial: 'ウォーターマーク付き素材',
    unknownSourceMaterial: '出典不明素材',
    reuseContentRisk: 'コンテンツ再利用リスク',
    exaggeration: '誇張表現',
    innerThoughtClaim: '心情の断定',
    politicalClaim: '政治的主張',
    adSuitabilityRisk: '広告適合性リスク',
  };

  return (
    <div className="lg:ml-64 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link href="/videos" className="text-sm text-blue-600 hover:underline">
            &larr; 動画一覧に戻る
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-gray-900">
            {video.title || video.projectName}
          </h1>
          <div className="mt-1 flex items-center gap-3">
            <StatusBadge status={video.status} />
            <span className="text-sm text-gray-500">{video.videoType}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Link
            href={`/videos/${id}/edit`}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            編集
          </Link>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            {deleting ? '削除中...' : '削除'}
          </button>
        </div>
      </div>

      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4">
          <h3 className="text-sm font-semibold text-yellow-800 mb-2">警告</h3>
          <ul className="space-y-1">
            {warnings.map((w, i) => (
              <li key={i} className="text-sm text-yellow-700">- {w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Score Summary */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
        {[
          { label: '利益', value: `¥${profit.toLocaleString()}`, color: profit >= 0 ? 'text-green-600' : 'text-red-600' },
          { label: 'ROI', value: video.totalCost > 0 ? `${roi.toFixed(1)}%` : '---', color: roi >= 100 ? 'text-green-600' : 'text-gray-900' },
          { label: '回収状況', value: recoveryStatus, color: 'text-gray-900' },
          { label: '動画スコア', value: `${videoScore}点`, color: videoScore >= 60 ? 'text-green-600' : videoScore >= 30 ? 'text-yellow-600' : 'text-red-600' },
          { label: '修正負担', value: `${revisionBurden.toFixed(0)}`, color: revisionBurden > 50 ? 'text-red-600' : 'text-gray-900' },
        ].map((item) => (
          <div key={item.label} className="rounded-lg border border-gray-200 bg-white p-4">
            <div className="text-xs text-gray-500">{item.label}</div>
            <div className={`mt-1 text-lg font-bold ${item.color}`}>{item.value}</div>
          </div>
        ))}
      </div>

      {/* 基本情報 */}
      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">基本情報</h2>
        <dl>
          <InfoRow label="企画名" value={video.projectName} />
          <InfoRow label="タイトル" value={video.title} />
          <InfoRow label="動画種別" value={video.videoType} />
          <InfoRow label="シリーズ名" value={video.seriesName} />
          <InfoRow label="テーマ" value={video.theme} />
          <InfoRow label="ステータス" value={<StatusBadge status={video.status} />} />
          <InfoRow label="外注者" value={video.outsourcer?.name} />
          <InfoRow label="依頼日" value={formatDate(video.requestDate)} />
          <InfoRow label="初稿期限" value={formatDate(video.firstDraftDue)} />
          <InfoRow label="納品期限" value={formatDate(video.deliveryDue)} />
          <InfoRow label="投稿日" value={formatDate(video.postDate)} />
          <InfoRow label="公開URL" value={
            video.publicUrl ? (
              <a href={video.publicUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                {video.publicUrl}
              </a>
            ) : null
          } />
        </dl>
      </section>

      {/* 費用 */}
      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">費用</h2>
        <dl>
          <InfoRow label="台本費" value={`¥${video.scriptCost.toLocaleString()}`} />
          <InfoRow label="編集費" value={`¥${video.editingCost.toLocaleString()}`} />
          <InfoRow label="Shorts編集費" value={`¥${video.shortsEditCost.toLocaleString()}`} />
          <InfoRow label="サムネイル費" value={`¥${video.thumbnailCost.toLocaleString()}`} />
          <InfoRow label="素材費" value={`¥${video.materialCost.toLocaleString()}`} />
          <InfoRow label="BGM費" value={`¥${video.bgmCost.toLocaleString()}`} />
          <InfoRow label="その他費用" value={`¥${video.otherCost.toLocaleString()}`} />
          <InfoRow label="合計費用" value={<span className="font-bold">¥{video.totalCost.toLocaleString()}</span>} />
        </dl>
      </section>

      {/* YouTube数値 */}
      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">YouTube数値</h2>
        {video.metrics ? (
          <dl>
            <InfoRow label="24時間再生数" value={video.metrics.views24h?.toLocaleString()} />
            <InfoRow label="48時間再生数" value={video.metrics.views48h?.toLocaleString()} />
            <InfoRow label="7日間再生数" value={video.metrics.views7d?.toLocaleString()} />
            <InfoRow label="30日間再生数" value={video.metrics.views30d?.toLocaleString()} />
            <InfoRow label="総再生数" value={video.metrics.totalViews?.toLocaleString()} />
            <InfoRow label="インプレッション" value={video.metrics.impressions?.toLocaleString()} />
            <InfoRow label="CTR" value={video.metrics.ctr != null ? `${video.metrics.ctr}%` : null} />
            <InfoRow label="平均視聴時間" value={video.metrics.avgWatchTime != null ? `${video.metrics.avgWatchTime}分` : null} />
            <InfoRow label="平均維持率" value={video.metrics.avgRetention != null ? `${video.metrics.avgRetention}%` : null} />
            <InfoRow label="高評価数" value={video.metrics.likes?.toLocaleString()} />
            <InfoRow label="コメント数" value={video.metrics.comments?.toLocaleString()} />
            <InfoRow label="登録者増加" value={video.metrics.subscribersGained?.toLocaleString()} />
            <InfoRow label="推定収益" value={video.metrics.estimatedRevenue != null ? `¥${video.metrics.estimatedRevenue.toLocaleString()}` : null} />
            <InfoRow label="RPM" value={video.metrics.rpm != null ? `¥${video.metrics.rpm.toLocaleString()}` : null} />
          </dl>
        ) : (
          <p className="text-sm text-gray-500">データなし</p>
        )}
      </section>

      {/* 品質管理 */}
      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">品質管理</h2>
        {video.quality ? (
          <dl>
            <InfoRow label="初稿修正回数" value={video.quality.firstDraftRevisions} />
            <InfoRow label="重大修正回数" value={video.quality.majorRevisions} />
            <InfoRow label="軽微修正回数" value={video.quality.minorRevisions} />
            <InfoRow label="誤字脱字" value={video.quality.typoErrors} />
            <InfoRow label="読み間違い" value={video.quality.voiceMisreads} />
            <InfoRow label="字幕ミスマッチ" value={video.quality.subtitleMismatch} />
            <InfoRow label="素材ミスマッチ" value={video.quality.materialMismatch} />
            <InfoRow label="レビュー時間" value={video.quality.reviewTime != null ? `${video.quality.reviewTime}分` : null} />
            <InfoRow label="最終スコア" value={video.quality.finalScore != null ? `${video.quality.finalScore}点` : null} />
          </dl>
        ) : (
          <p className="text-sm text-gray-500">データなし</p>
        )}
      </section>

      {/* 権利リスク */}
      <section className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-4 text-lg font-semibold text-gray-900">権利リスク</h2>
        {video.risks.length > 0 ? (
          video.risks.map((risk) => (
            <div key={risk.id} className="mb-4 last:mb-0">
              <div className="mb-2 flex items-center gap-2">
                <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${
                  risk.riskLevel === '高' || risk.riskLevel === '公開不可' ? 'bg-red-100 text-red-700' :
                  risk.riskLevel === '中' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-green-100 text-green-700'
                }`}>
                  リスクレベル: {risk.riskLevel}
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {riskBooleanFields.map((field) =>
                  risk[field] ? (
                    <span key={field} className="rounded bg-red-50 px-2 py-1 text-xs text-red-700 border border-red-200">
                      {riskLabels[field]}
                    </span>
                  ) : null
                )}
              </div>
              {risk.notes && <p className="mt-2 text-sm text-gray-600">{risk.notes}</p>}
            </div>
          ))
        ) : (
          <p className="text-sm text-gray-500">リスク情報なし</p>
        )}
      </section>

      {/* Growth Analysis */}
      {(growthFactors.positive.length > 0 || growthFactors.negative.length > 0) && (
        <section className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">成長要因分析</h2>
          {growthFactors.positive.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-green-700 mb-1">ポジティブ要因</h3>
              <ul className="space-y-1">
                {growthFactors.positive.map((f, i) => (
                  <li key={i} className="text-sm text-green-600">+ {f}</li>
                ))}
              </ul>
            </div>
          )}
          {growthFactors.negative.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-red-700 mb-1">ネガティブ要因</h3>
              <ul className="space-y-1">
                {growthFactors.negative.map((f, i) => (
                  <li key={i} className="text-sm text-red-600">- {f}</li>
                ))}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* Improvement Suggestions */}
      {suggestions.length > 0 && (
        <section className="rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-lg font-semibold text-gray-900">改善提案</h2>
          <ul className="space-y-2">
            {suggestions.map((s, i) => (
              <li key={i} className="text-sm text-gray-700">{s}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
