interface Warning {
  videoId: string;
  title: string;
  messages: string[];
}

export default function WarningBanner({ warnings }: { warnings: Warning[] }) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="rounded-lg border border-amber-300 bg-amber-50 p-4">
      <div className="flex items-start gap-3">
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          className="shrink-0 mt-0.5 text-amber-600"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M10 2l8 14H2L10 2z" />
          <path d="M10 8v4M10 14h.01" />
        </svg>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-amber-800">
            注意が必要な動画 ({warnings.length}件)
          </h3>
          <ul className="mt-2 space-y-2">
            {warnings.map((warning) => (
              <li key={warning.videoId}>
                <p className="text-sm font-medium text-amber-900">
                  {warning.title}
                </p>
                <ul className="mt-0.5 space-y-0.5">
                  {warning.messages.map((msg, i) => (
                    <li
                      key={i}
                      className="text-sm text-amber-700 pl-3 relative before:content-['・'] before:absolute before:left-0"
                    >
                      {msg}
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
