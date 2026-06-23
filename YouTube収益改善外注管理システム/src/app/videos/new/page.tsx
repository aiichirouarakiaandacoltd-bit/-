'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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

const STATUSES = ['企画中', '台本作成中', '制作中', '修正中', '納品済み', '公開済み', '非公開'] as const;
const VIDEO_TYPES = ['長尺', 'Shorts'] as const;

export default function NewVideoPage() {
  const router = useRouter();
  const [outsourcers, setOutsourcers] = useState<Outsourcer[]>([]);
  const [activeTab, setActiveTab] = useState<'basic' | 'cost'>('basic');
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    watch,
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
    async function fetchOutsourcers() {
      try {
        const res = await fetch('/api/outsourcers');
        if (res.ok) setOutsourcers(await res.json());
      } catch (err) {
        console.error('Failed to fetch outsourcers:', err);
      }
    }
    fetchOutsourcers();
  }, []);

  async function onSubmit(data: VideoFormData) {
    setSubmitting(true);
    try {
      // Clean empty strings to undefined
      const body: Record<string, unknown> = { ...data };
      for (const key of Object.keys(body)) {
        if (body[key] === '') body[key] = undefined;
      }

      const res = await fetch('/api/videos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (res.ok) {
        router.push('/videos');
      } else {
        const err = await res.json();
        alert(err.error || '作成に失敗しました');
      }
    } catch {
      alert('作成に失敗しました');
    } finally {
      setSubmitting(false);
    }
  }

  const tabs = [
    { key: 'basic' as const, label: '基本情報' },
    { key: 'cost' as const, label: '費用' },
  ];

  const inputClass = 'block w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500';
  const labelClass = 'block text-sm font-medium text-gray-700 mb-1';
  const errorClass = 'mt-1 text-xs text-red-600';

  return (
    <div className="lg:ml-64">
      <div className="mb-6">
        <Link href="/videos" className="text-sm text-blue-600 hover:underline">
          &larr; 動画一覧に戻る
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-gray-900">新規動画作成</h1>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Tabs */}
        <div className="border-b border-gray-200">
          <nav className="flex gap-4">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`border-b-2 px-1 py-3 text-sm font-medium transition-colors ${
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

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            href="/videos"
            className="rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            キャンセル
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-lg bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {submitting ? '作成中...' : '作成'}
          </button>
        </div>
      </form>
    </div>
  );
}
