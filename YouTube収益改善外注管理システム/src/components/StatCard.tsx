const borderColors: Record<string, string> = {
  blue: 'border-l-blue-500',
  green: 'border-l-green-500',
  red: 'border-l-red-500',
  yellow: 'border-l-yellow-500',
  gray: 'border-l-gray-400',
};

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  color?: 'blue' | 'green' | 'red' | 'yellow' | 'gray';
}

export default function StatCard({
  title,
  value,
  subtitle,
  color = 'blue',
}: StatCardProps) {
  const borderClass = borderColors[color];

  return (
    <div
      className={`rounded-lg border border-gray-200 border-l-4 ${borderClass} bg-white p-5 shadow-sm`}
    >
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">{value}</p>
      {subtitle && (
        <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
      )}
    </div>
  );
}
