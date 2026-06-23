"use client";

import { useState } from "react";

export default function SettingsPage() {
  const [channelName, setChannelName] = useState("");
  const [seeding, setSeeding] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  async function handleSeed() {
    setSeeding(true);
    setMessage(null);

    try {
      const res = await fetch("/api/seed", { method: "POST" });
      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.error || "サンプルデータの投入に失敗しました");
      }

      setMessage({ type: "success", text: json.message });
    } catch (err) {
      setMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "サンプルデータの投入に失敗しました",
      });
    } finally {
      setSeeding(false);
    }
  }

  async function handleDeleteAll() {
    const confirmed = window.confirm(
      "全てのデータを削除します。この操作は元に戻せません。本当に削除しますか？"
    );
    if (!confirmed) return;

    setMessage(null);

    try {
      const res = await fetch("/api/seed", { method: "DELETE" });

      if (!res.ok) {
        const json = await res.json();
        throw new Error(json.error || "データの削除に失敗しました");
      }

      setMessage({ type: "success", text: "全てのデータを削除しました" });
    } catch (err) {
      setMessage({
        type: "error",
        text:
          err instanceof Error ? err.message : "データの削除に失敗しました",
      });
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">設定</h1>

      {message && (
        <div
          className={`rounded-md p-4 ${
            message.type === "success"
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-red-50 text-red-800 border border-red-200"
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Channel Settings */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          チャンネル設定
        </h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              チャンネル名
            </label>
            <input
              type="text"
              value={channelName}
              onChange={(e) => setChannelName(e.target.value)}
              placeholder="チャンネル名を入力"
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full max-w-md"
            />
          </div>
          <button
            onClick={() =>
              setMessage({ type: "success", text: "設定を保存しました" })
            }
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium transition-colors"
          >
            保存
          </button>
        </div>
      </div>

      {/* Data Management */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          データ管理
        </h2>
        <div className="space-y-4">
          <div>
            <p className="text-sm text-gray-500 mb-2">
              テスト用のサンプルデータを投入します。
            </p>
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {seeding ? "投入中..." : "サンプルデータを投入"}
            </button>
          </div>
          <div className="border-t border-gray-200 pt-4">
            <p className="text-sm text-red-500 mb-2">
              全てのデータを削除します。この操作は元に戻せません。
            </p>
            <button
              onClick={handleDeleteAll}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium transition-colors"
            >
              データを全削除
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
