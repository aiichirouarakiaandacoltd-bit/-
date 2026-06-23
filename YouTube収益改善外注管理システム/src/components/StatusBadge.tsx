const statusColors: Record<string, string> = {
  '企画中': 'bg-gray-100 text-gray-700',
  '台本作成中': 'bg-yellow-100 text-yellow-800',
  '制作中': 'bg-blue-100 text-blue-700',
  '修正中': 'bg-orange-100 text-orange-700',
  '納品済み': 'bg-green-100 text-green-700',
  '公開済み': 'bg-emerald-100 text-emerald-700',
  '非公開': 'bg-red-100 text-red-700',
};

export default function StatusBadge({ status }: { status: string }) {
  const colorClasses = statusColors[status] ?? 'bg-gray-100 text-gray-700';

  return (
    <span
      className={`inline-block rounded-full px-2 py-0.5 text-xs font-semibold ${colorClasses}`}
    >
      {status}
    </span>
  );
}
