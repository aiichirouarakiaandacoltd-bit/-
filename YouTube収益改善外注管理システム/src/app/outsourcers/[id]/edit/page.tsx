'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import Link from 'next/link';

const outsourcerSchema = z.object({
  name: z.string().min(1, '氏名は必須です'),
  serviceName: z.string().optional().default(''),
  contact: z.string().optional().default(''),
  availableTasks: z.string().optional().default(''),
  longVideoPrice: z.coerce.number().min(0, '0以上で入力してください').default(0),
  shortsPrice: z.coerce.number().min(0, '0以上で入力してください').default(0),
  thumbnailPrice: z.coerce.number().min(0, '0以上で入力してください').default(0),
  deliveryDays: z.coerce.number().min(0, '0以上で入力してください').optional(),
  software: z.string().optional().default(''),
  voicevoxCapable: z.boolean().default(false),
  materialCapable: z.boolean().default(false),
  thumbnailCapable: z.boolean().default(false),
  continuationOk: z.boolean().default(true),
  continuationStatus: z.string().default('テスト継続'),
  notes: z.string().optional().default(''),
});

type OutsourcerFormData = z.infer<typeof outsourcerSchema>;

export default function EditOutsourcerPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  } = useForm<OutsourcerFormData>({
    resolver: zodResolver(outsourcerSchema) as any,
  });

  useEffect(() => {
    if (!params.id) return;
    fetch(`/api/outsourcers/${params.id}`)
      .then((res) => {
        if (!res.ok) throw new Error('外注先の取得に失敗しました');
        return res.json();
      })
      .then((data) => {
        reset({
          name: data.name || '',
          serviceName: data.serviceName || '',
          contact: data.contact || '',
          availableTasks: data.availableTasks || '',
          longVideoPrice: data.longVideoPrice ?? 0,
          shortsPrice: data.shortsPrice ?? 0,
          thumbnailPrice: data.thumbnailPrice ?? 0,
          deliveryDays: data.deliveryDays ?? undefined,
          software: data.software || '',
          voicevoxCapable: data.voicevoxCapable ?? false,
          materialCapable: data.materialCapable ?? false,
          thumbnailCapable: data.thumbnailCapable ?? false,
          continuationOk: data.continuationOk ?? true,
          continuationStatus: data.continuationStatus || 'テスト継続',
          notes: data.notes || '',
        });
      })
      .catch((err) => setFetchError(err.message))
      .finally(() => setLoading(false));
  }, [params.id, reset]);

  const onSubmit = async (data: OutsourcerFormData) => {
    try {
      const res = await fetch(`/api/outsourcers/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error('更新に失敗しました');
      router.push(`/outsourcers/${params.id}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : '更新に失敗しました');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">読み込み中...</p>
      </div>
    );
  }

  if (fetchError) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-red-500">{fetchError}</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-6">
        <Link
          href={`/outsourcers/${params.id}`}
          className="text-sm text-blue-600 hover:underline"
        >
          &larr; 詳細に戻る
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 mt-1">外注先 編集</h1>
      </div>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="bg-white shadow rounded-lg p-6 space-y-6"
      >
        {/* 氏名 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            氏名 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('name')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* サービス名 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            サービス名
          </label>
          <input
            type="text"
            {...register('serviceName')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 連絡先 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            連絡先
          </label>
          <input
            type="text"
            {...register('contact')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* 担当業務 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            担当業務
          </label>
          <input
            type="text"
            {...register('availableTasks')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="例: 動画編集, サムネイル作成"
          />
        </div>

        {/* 単価 */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              長尺単価 (円)
            </label>
            <input
              type="number"
              {...register('longVideoPrice')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.longVideoPrice && (
              <p className="mt-1 text-sm text-red-600">
                {errors.longVideoPrice.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Shorts単価 (円)
            </label>
            <input
              type="number"
              {...register('shortsPrice')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.shortsPrice && (
              <p className="mt-1 text-sm text-red-600">
                {errors.shortsPrice.message}
              </p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              サムネイル単価 (円)
            </label>
            <input
              type="number"
              {...register('thumbnailPrice')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            {errors.thumbnailPrice && (
              <p className="mt-1 text-sm text-red-600">
                {errors.thumbnailPrice.message}
              </p>
            )}
          </div>
        </div>

        {/* 納期・ソフト */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              納期 (日)
            </label>
            <input
              type="number"
              {...register('deliveryDays')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              使用ソフト
            </label>
            <input
              type="text"
              {...register('software')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* 対応可能チェックボックス */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            対応可能
          </label>
          <div className="flex flex-wrap gap-6">
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                {...register('voicevoxCapable')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              VOICEVOX対応
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                {...register('materialCapable')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              素材提供対応
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input
                type="checkbox"
                {...register('thumbnailCapable')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              サムネイル対応
            </label>
          </div>
        </div>

        {/* 継続 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-700">
              <input
                type="checkbox"
                {...register('continuationOk')}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              継続OK
            </label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              継続判定
            </label>
            <select
              {...register('continuationStatus')}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="テスト継続">テスト継続</option>
              <option value="継続OK">継続OK</option>
              <option value="要検討">要検討</option>
              <option value="停止">停止</option>
            </select>
          </div>
        </div>

        {/* 備考 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            備考
          </label>
          <textarea
            {...register('notes')}
            rows={4}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-3">
          <Link
            href={`/outsourcers/${params.id}`}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            キャンセル
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? '更新中...' : '更新する'}
          </button>
        </div>
      </form>
    </div>
  );
}
