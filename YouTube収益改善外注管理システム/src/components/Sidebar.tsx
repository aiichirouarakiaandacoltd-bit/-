'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const navItems = [
  {
    label: 'ダッシュボード',
    href: '/',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="10" width="4" height="8" rx="0.5" />
        <rect x="8" y="6" width="4" height="12" rx="0.5" />
        <rect x="14" y="2" width="4" height="16" rx="0.5" />
      </svg>
    ),
  },
  {
    label: '動画一覧',
    href: '/videos',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
        <path d="M6.5 4.5v11l9-5.5-9-5.5z" />
      </svg>
    ),
  },
  {
    label: '外注者一覧',
    href: '/outsourcers',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
        <circle cx="7" cy="7" r="3" />
        <circle cx="13" cy="7" r="3" />
        <path d="M1 17c0-3 2.5-5 6-5s6 2 6 5" />
        <path d="M10 17c0-3 2.5-5 6-5s3 2 3 5" opacity="0.6" />
      </svg>
    ),
  },
  {
    label: '制作進捗',
    href: '/progress',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="8" />
        <path d="M10 5v5l3.5 3.5" />
      </svg>
    ),
  },
  {
    label: '収益分析',
    href: '/analytics',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 17l4-6 4 3 6-10" />
        <path d="M14 4h3v3" />
      </svg>
    ),
  },
  {
    label: '権利リスク',
    href: '/risks',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10 2l7 4v5c0 4-3 7-7 9-4-2-7-5-7-9V6l7-4z" />
      </svg>
    ),
  },
  {
    label: '月次レポート',
    href: '/reports',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 2h7l4 4v12a1 1 0 01-1 1H5a1 1 0 01-1-1V3a1 1 0 011-1z" />
        <path d="M12 2v4h4" />
        <path d="M7 10h6M7 13h4" />
      </svg>
    ),
  },
  {
    label: 'CSV入出力',
    href: '/csv',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="3" width="16" height="14" rx="1" />
        <path d="M2 7h16M2 11h16M2 15h16M7 3v14M13 3v14" />
      </svg>
    ),
  },
  {
    label: '設定',
    href: '/settings',
    icon: (
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="10" cy="10" r="3" />
        <path d="M10 1v3M10 16v3M3.5 3.5l2 2M14.5 14.5l2 2M1 10h3M16 10h3M3.5 16.5l2-2M14.5 5.5l2-2" />
      </svg>
    ),
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/';
    return pathname.startsWith(href);
  };

  const sidebarContent = (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-5 border-b border-gray-200">
        <h1 className="text-lg font-bold text-gray-900">YT収益管理</h1>
        <button
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-1 rounded text-gray-500 hover:bg-gray-100"
          aria-label="メニューを閉じる"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M5 5l10 10M15 5L5 15" />
          </svg>
        </button>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span className="shrink-0">{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-40 lg:hidden p-2 rounded-lg bg-white shadow-md text-gray-700 hover:bg-gray-100"
        aria-label="メニューを開く"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M3 5h14M3 10h14M3 15h14" />
        </svg>
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-200 ease-in-out lg:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-col lg:fixed lg:inset-y-0 lg:left-0 lg:w-64 bg-white border-r border-gray-200">
        {sidebarContent}
      </aside>
    </>
  );
}
