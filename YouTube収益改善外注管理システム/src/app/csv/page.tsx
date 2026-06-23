"use client";

import { useState } from "react";

export default function CsvPage() {
  const [importType, setImportType] = useState<string>("videos");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  async function handleExport(type: string) {
    try {
      const res = await fetch(`/api/csv?type=${type}`);
      if (!res.ok) throw new Error("エクスポートに失敗しました");

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type}_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch {
      setMessage({ type: "error", text: "エクスポートに失敗しました" });
    }
  }

  async function handleImport() {
    if (!file) {
      setMessage({ type: "error", text: "ファイルを選択してください" });
      return;
    }

    setUploading(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("type", importType);

      const res = await fetch("/api/csv", {
        method: "POST",
        body: formData,
      });

      const json = await res.json();

      if (!res.ok) {
        throw new Error(json.error || "インポートに失敗しました");
      }

      setMessage({ type: "success", text: json.message });
      setFile(null);
      // Reset file input
      const fileInput = document.querySelector(
        'input[type="file"]'
      ) as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (err) {
      setMessage({
        type: "error",
        text: err instanceof Error ? err.message : "インポートに失敗しました",
      });
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">CSVインポート/エクスポート</h1>

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

      {/* Export Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          エクスポート
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          データをCSVファイルとしてダウンロードします。
        </p>
        <div className="flex gap-4">
          <button
            onClick={() => handleExport("videos")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium transition-colors"
          >
            動画データをエクスポート
          </button>
          <button
            onClick={() => handleExport("outsourcers")}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium transition-colors"
          >
            外注者データをエクスポート
          </button>
        </div>
      </div>

      {/* Import Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          インポート
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          CSVファイルからデータをインポートします。
        </p>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              データ種別
            </label>
            <select
              value={importType}
              onChange={(e) => setImportType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full max-w-xs"
            >
              <option value="videos">動画データ</option>
              <option value="outsourcers">外注者データ</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              CSVファイル
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="block w-full max-w-md text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
          <button
            onClick={handleImport}
            disabled={uploading || !file}
            className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {uploading ? "インポート中..." : "インポート"}
          </button>
        </div>
      </div>
    </div>
  );
}
