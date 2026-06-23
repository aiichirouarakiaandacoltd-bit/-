'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod/v3';

const videoSchema = z.object({
  projectName: z.string().min(1, '企画名は必須です'),
  title: z.string().optional(),
  videoType: z.string().default('長尺'),
  seriesName: z.string().optional(),
  theme: z.string().optional(),
  outsourcerId: z.string().optional(),
  status: z.string().default('企画中'),
  requestDate: z.string().optional(),
  firstDraftDue: z.string().optional(),
  deliveryDue: z.string().optional(),
  postDate: z.string().optional(),
  publicUrl: z.string().optional(),
  scriptCost: z.coerce.number().min(0).default(0),
  editingCost: z.coerce.number().min(0).default(0),
  shortsEditCost: z.coerce.number().min(0).default(0),
  thumbnailCost: z.coerce.number().min(0).default(0),
  materialCost: z.coerce.number().min(0).default(0),
  bgmCost: z.coerce.number().min(0).default(0),
  otherCost: z.coerce.number().min(0).default(0),
});

type VideoFormData = z.infer<typeof videoSchema>;

interface Outsourcer {
  id: string;
  name: string;
}

interface VideoMetrics {
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
}

interface VideoQuality {
  firstDraftRevisions: number;
  majorRevisions: number;
  minorRevisions: number;
  typoErrors: number;
  voiceMisreads: number;
  subtitleMismatch: number;
  materialMismatch: number;
  reviewTime: number | null;
}

interface VideoRiskEntry {
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
}

const STATUSES = ['企画中', '台本作成中', '制作中', '修正中', '納品済み', '公開済み', '非公開'] as const;
const VIDEO_TYPES = ['長尺', 'Shorts'] as const;

function formatDateForInput(dateStr: string | null | undefined): string {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toISOString().split('T')[0];
  } catch {
    return '';
  }
}

export default function EditVideoPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [outsourcers, setOutsourcers] = useState<Outsourcer[]>([]);
  const [activeTab, setActiveTab] = useState<'basic' | 'cost' | 'metrics' | 'quality' | 'risks'>('basic');
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState<VideoMetrics | null>(null);
  const [quality, setQuality] = useState<VideoQuality | null>(null);
  const [risks, setRisks] = useState<VideoRiskEntry[]>([]);

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<VideoFormData>({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolver: zodResolver(videoSchema) as any,
    defaultValues: {
      videoType: '長尺',
      status: '企画中',
      scriptCost: 0,
      editingCost: 0,
      shortsEditCost: 0,
      thumbnailCost: 0,
      materialCost: 0,
      bgmCost: 0,
      otherCost: 0,
    },
  });

  const costFields = watch(['scriptCost', 'editingCost', 'shortsEditCost', 'thumbnailCost', 'materialCost', 'bgmCost', 'otherCost']);
  const totalCost = costFields.reduce((sum, v) => sum + (Number(v) || 0), 0);

  useEffect(() => {
    async function fetchData() {
      try {
        const [videoRes, outsourcersRes] = await Promise.all([
          fetch(`/api/videos/${id}`),
          fetch('/api/outsourcers'),
        ]);

        if (outsourcersRes.ok) {
          setOutsourcers(await outsourcersRes.json());
        }

        if (videoRes.ok) {
          const video = await videoRes.json();
          reset({
            projectName: video.projectName || '',
            title: video.title || '',
            videoType: video.videoType || '長尺',
            seriesName: video.seriesName || '',
            theme: video.theme || '',
            outsourcerId: video.outsourcerId || '',
            status: video.status || '企画中',
            requestDate: formatDateForInput(video.requestDate),
            firstDraftDue: formatDateForInput(video.firstDraftDue),
            deliveryDue: formatDateForInput(video.deliveryDue),
            postDate: formatDateForInput(video.postDate),
            publicUrl: video.publicUrl || '',
            scriptCost: video.scriptCost ?? 0,
            editingCost: video.editingCost ?? 0,
            shortsEditCost: video.shortsEditCost ?? 0,
            thumbnailCost: video.thumbnailCost ?? 0,
            materialCost: video.materialCost ?? 0,
            bgmCost: video.bgmCost ?? 0,
            otherCost: video.otherCost ?? 0,
          });
          setMetrics(video.metrics ?? null);
          setQuality(video.quality ?? null);
          setRisks(video.risks ?? []);
        }
      } catch (err) {
        console.error('Failed to fetch data:', err);
      } finally {
        setLoading(false);
      }
    }
    if (id) fetchData();
  }, [id, reset]);

  async function onSubmit(data: VideoFormData) {
    setSubmitting(true);
    try {
      const body: Record<string, unknown> = { ...data };
      for (const key of Object.keys(body)) {
        if (body[key] === '') body[key] = undefined;
      }

      const res = await fetch(`/api/videos/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        router.push(`/videos/${id}`);
      } else {
        const err = await res.json();
        alert(err.error || '更新に失敗しました');
      }
    } catch {
      alert('更新に失敗しました');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="lg:ml-64 flex items-center justify-center py-12">
        <div className="text-gray-500">読み込み中...</div>
      </div>
    );
  }

  const tabs = [
    { key: 'basic' as const, label: '基本情報' },
    { key: 'cost' as const, label: '費用' },
    { key: 'metrics' as const, label: 'YouTube数値' },
    { key: 'quality' as const, label: '品質管理' },
    { key: 'risks' as const, label: '権利リスク' },
  ];

  const inputClass = 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';
  const readonlyClass = 'block w-full rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm text-gray-600';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1';
  const errorClass = 'mt-1 text-xs text-red-600';

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

  const riskBooleanFields = Object.keys(riskLabels) as Array<keyof typeof riskLabels>;

  return (
    <div className="lg:ml-64">
      <div className="mb-6">
        <Link href={`/videos/${id}`} className="text-sm text-blue-600 hover:underline">
          &larr; 詳細に戻る
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">動画編集</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex gap-4 overflow-x-auto">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`whitespace-nowrap border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* 基本情報 */}
        {activeTab === 'basic' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
            <div>
              <label className={labelClass}>企画名 <span className="text-red-500">*</span></label>
              <input {...register('projectName')} className={inputClass} placeholder="企画名を入力" />
              {errors.projectName && <p className={errorClass}>{errors.projectName.message}</p>}
            </div>

            <div>
              <label className={labelClass}>タイトル</label>
              <input {...register('title')} className={inputClass} placeholder="動画タイトル" />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className={labelClass}>動画種別</label>
                <select {...register('videoType')} className={inputClass}>
                  {VIDEO_TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className={labelClass}>ステータス</label>
                <select {...register('status')} className={inputClass}>
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className={labelClass}>シリーズ名</label>
                <input {...register('seriesName')} className={inputClass} placeholder="シリーズ名" />
              </div>
              <div>
                <label className={labelClass}>テーマ</label>
                <input {...register('theme')} className={inputClass} placeholder="テーマ" />
              </div>
            </div>

            <div>
              <label className={labelClass}>外注者</label>
              <select {...register('outsourcerId')} className={inputClass}>
                <option value="">選択してください</option>
                {outsourcers.map((o) => (
                  <option key={o.id} value={o.id}>{o.name}</option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label className={labelClass}>依頼日</label>
                <input type="date" {...register('requestDate')} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>初稿期限</label>
                <input type="date" {...register('firstDraftDue')} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>納品期限</label>
                <input type="date" {...register('deliveryDue')} className={inputClass} />
              </div>
              <div>
                <label className={labelClass}>投稿日</label>
                <input type="date" {...register('postDate')} className={inputClass} />
              </div>
            </div>

            <div>
              <label className={labelClass}>公開URL</label>
              <input {...register('publicUrl')} className={inputClass} placeholder="https://youtube.com/watch?v=..." />
            </div>
          </div>
        )}

        {/* 費用 */}
        {activeTab === 'cost' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
            {[
              { name: 'scriptCost' as const, label: '台本費' },
              { name: 'editingCost' as const, label: '編集費' },
              { name: 'shortsEditCost' as const, label: 'Shorts編集費' },
              { name: 'thumbnailCost' as const, label: 'サムネイル費' },
              { name: 'materialCost' as const, label: '素材費' },
              { name: 'bgmCost' as const, label: 'BGM費' },
              { name: 'otherCost' as const, label: 'その他費用' },
            ].map((field) => (
              <div key={field.name}>
                <label className={labelClass}>{field.label}</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-gray-500">¥</span>
                  <input
                    type="number"
                    {...register(field.name)}
                    className={`${inputClass} pl-7`}
                    min={0}
                  />
                </div>
              </div>
            ))}

            <div className="border-t border-gray-200 pt-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-900">合計費用</span>
                <span className="text-lg font-bold text-gray-900">¥{totalCost.toLocaleString()}</span>
              </div>
            </div>
          </div>
        )}

        {/* YouTube数値 (read-only) */}
        {activeTab === 'metrics' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
            <p className="text-sm text-gray-500 mb-4">YouTube数値は閲覧のみです。別途APIで更新してください。</p>
            {metrics ? (
              <>
                {[
                  { label: '24時間再生数', value: metrics.views24h },
                  { label: '48時間再生数', value: metrics.views48h },
                  { label: '7日間再生数', value: metrics.views7d },
                  { label: '30日間再生数', value: metrics.views30d },
                  { label: '総再生数', value: metrics.totalViews },
                  { label: 'インプレッション', value: metrics.impressions },
                  { label: 'CTR (%)', value: metrics.ctr },
                  { label: '平均視聴時間 (分)', value: metrics.avgWatchTime },
                  { label: '平均維持率 (%)', value: metrics.avgRetention },
                  { label: '高評価数', value: metrics.likes },
                  { label: 'コメント数', value: metrics.comments },
                  { label: '登録者増加', value: metrics.subscribersGained },
                  { label: '推定収益', value: metrics.estimatedRevenue != null ? `¥${metrics.estimatedRevenue.toLocaleString()}` : null },
                  { label: 'RPM', value: metrics.rpm != null ? `¥${metrics.rpm.toLocaleString()}` : null },
                ].map((item) => (
                  <div key={item.label}>
                    <label className={labelClass}>{item.label}</label>
                    <div className={readonlyClass}>
                      {item.value != null ? String(item.value) : '---'}
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <p className="text-sm text-gray-500">データなし</p>
            )}
          </div>
        )}

        {/* 品質管理 (read-only) */}
        {activeTab === 'quality' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
            <p className="text-sm text-gray-500 mb-4">品質管理データは閲覧のみです。別途APIで更新してください。</p>
            {quality ? (
              <>
                {[
                  { label: '初稿修正回数', value: quality.firstDraftRevisions },
                  { label: '重大修正回数', value: quality.majorRevisions },
                  { label: '軽微修正回数', value: quality.minorRevisions },
                  { label: '誤字脱字', value: quality.typoErrors },
                  { label: '読み間違い', value: quality.voiceMisreads },
                  { label: '字幕ミスマッチ', value: quality.subtitleMismatch },
                  { label: '素材ミスマッチ', value: quality.materialMismatch },
                  { label: 'レビュー時間 (分)', value: quality.reviewTime },
                ].map((item) => (
                  <div key={item.label}>
                    <label className={labelClass}>{item.label}</label>
                    <div className={readonlyClass}>
                      {item.value != null ? String(item.value) : '---'}
                    </div>
                  </div>
                ))}
              </>
            ) : (
              <p className="text-sm text-gray-500">データなし</p>
            )}
          </div>
        )}

        {/* 権利リスク (read-only) */}
        {activeTab === 'risks' && (
          <div className="rounded-lg border border-gray-200 bg-white p-6 space-y-4">
            <p className="text-sm text-gray-500 mb-4">権利リスクデータは閲覧のみです。別途APIで更新してください。</p>
            {risks.length > 0 ? (
              risks.map((risk) => (
                <div key={risk.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
                  <div>
                    <label className={labelClass}>リスクレベル</label>
                    <div className={readonlyClass}>{risk.riskLevel}</div>
                  </div>

                  <div>
                    <label className={labelClass}>該当リスク項目</label>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {riskBooleanFields.map((field) => (
                        <span
                          key={field}
                          className={`rounded px-2 py-1 text-xs border ${
                            risk[field as keyof VideoRiskEntry]
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-gray-50 text-gray-400 border-gray-200'
                          }`}
                        >
                          {risk[field as keyof VideoRiskEntry] ? '●' : '○'} {riskLabels[field]}
                        </span>
                      ))}
                    </div>
                  </div>

                  {risk.notes && (
                    <div>
                      <label className={labelClass}>備考</label>
                      <div className={readonlyClass}>{risk.notes}</div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-500">リスク情報なし</p>
            )}
          </div>
        )}

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            href={`/videos/${id}`}
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            キャンセル
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? '保存中...' : '保存'}
          </button>
        </div>
      </form>
    </div>
  );
}
