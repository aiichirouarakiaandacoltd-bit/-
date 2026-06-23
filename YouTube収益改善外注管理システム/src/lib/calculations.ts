export function calcProfit(revenue: number, cost: number): number {
  return revenue - cost;
}

export function calcROI(profit: number, cost: number): number {
  if (cost === 0) return 0;
  return (profit / cost) * 100;
}

export function calcRecoveryRate(revenue: number, cost: number): number {
  if (cost === 0) return 0;
  return (revenue / cost) * 100;
}

export function calcRecoveryStatus(revenue: number, cost: number): string {
  if (cost === 0) return "—";
  const rate = (revenue / cost) * 100;
  if (rate >= 200) return "利益化";
  if (rate >= 100) return "回収完了";
  if (rate >= 50) return "50％回収";
  return "未回収";
}

export function calcCostPer1000Views(cost: number, views: number): number {
  if (views === 0) return 0;
  return (cost / views) * 1000;
}

export function calcRevisionBurdenScore(
  revisions: number,
  majorRevisions: number,
  reviewTimeMinutes: number
): number {
  return Math.min(100, revisions * 5 + majorRevisions * 15 + reviewTimeMinutes * 0.5);
}

export function calcVideoScore(params: {
  totalViews?: number;
  ctr?: number;
  avgRetention?: number;
  profit: number;
  roi: number;
  subscribersGained?: number;
  comments?: number;
  views30d?: number;
  totalCost: number;
  revisionBurden: number;
  riskCount: number;
}): number {
  const {
    totalViews = 0,
    ctr = 0,
    avgRetention = 0,
    profit,
    roi,
    subscribersGained = 0,
    comments = 0,
    views30d = 0,
    totalCost,
    revisionBurden,
    riskCount,
  } = params;

  let score = 0;

  // 再生数 (15点)
  if (totalViews >= 100000) score += 15;
  else if (totalViews >= 50000) score += 12;
  else if (totalViews >= 10000) score += 9;
  else if (totalViews >= 5000) score += 6;
  else if (totalViews >= 1000) score += 3;

  // CTR (10点)
  if (ctr >= 10) score += 10;
  else if (ctr >= 7) score += 8;
  else if (ctr >= 5) score += 6;
  else if (ctr >= 3) score += 3;

  // 維持率 (10点)
  if (avgRetention >= 60) score += 10;
  else if (avgRetention >= 45) score += 8;
  else if (avgRetention >= 30) score += 5;
  else if (avgRetention >= 20) score += 3;

  // 利益 (15点)
  if (profit >= 10000) score += 15;
  else if (profit >= 5000) score += 12;
  else if (profit >= 1000) score += 8;
  else if (profit >= 0) score += 4;

  // ROI (10点)
  if (roi >= 300) score += 10;
  else if (roi >= 200) score += 8;
  else if (roi >= 100) score += 5;
  else if (roi >= 50) score += 2;

  // 登録者増加 (10点)
  if (subscribersGained >= 100) score += 10;
  else if (subscribersGained >= 50) score += 7;
  else if (subscribersGained >= 10) score += 4;
  else if (subscribersGained >= 1) score += 2;

  // コメント (5点)
  if (comments >= 50) score += 5;
  else if (comments >= 20) score += 3;
  else if (comments >= 5) score += 1;

  // 長期再生 (10点)
  if (views30d && totalViews) {
    const longTermRatio = views30d / totalViews;
    if (longTermRatio >= 0.7) score += 10;
    else if (longTermRatio >= 0.5) score += 7;
    else if (longTermRatio >= 0.3) score += 4;
  }

  // 制作原価の効率 (10点) - 低コストほど高評価
  if (totalCost <= 2000) score += 10;
  else if (totalCost <= 5000) score += 7;
  else if (totalCost <= 10000) score += 4;
  else if (totalCost <= 20000) score += 2;

  // 修正負担ペナルティ (最大-5点)
  score -= Math.min(5, revisionBurden * 0.05);

  // 権利リスクペナルティ (最大-5点)
  score -= Math.min(5, riskCount * 2);

  return Math.max(0, Math.min(100, Math.round(score)));
}

export function calcOutsourcerCostEfficiency(
  totalRevenue: number,
  totalCost: number
): number {
  if (totalCost === 0) return 0;
  return totalRevenue / totalCost;
}

export function generateWarnings(video: {
  status: string;
  deliveryDue?: string | null;
  totalCost: number;
  estimatedRevenue?: number;
  riskLevel?: string;
  paymentStatus?: string;
  revisionCount?: number;
}): string[] {
  const warnings: string[] = [];
  const now = new Date();

  if (video.deliveryDue) {
    const due = new Date(video.deliveryDue);
    const daysUntil = (due.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);
    if (daysUntil < 0 && video.status !== "公開済み" && video.status !== "納品済み") {
      warnings.push("納期を超過しています");
    } else if (daysUntil <= 2 && daysUntil >= 0 && video.status !== "公開済み" && video.status !== "納品済み") {
      warnings.push("納期が近づいています");
    }
  }

  if (video.totalCost > 0 && (video.estimatedRevenue || 0) < video.totalCost && video.status === "公開済み") {
    warnings.push("制作費が未回収です");
  }

  if (video.riskLevel === "高" || video.riskLevel === "公開不可") {
    warnings.push("権利リスクが高い動画です");
  }

  if (video.paymentStatus === "未払い") {
    warnings.push("支払いが未完了です");
  }

  if ((video.revisionCount || 0) >= 3) {
    warnings.push("修正回数が多くなっています");
  }

  return warnings;
}

export function analyzeGrowthFactors(metrics: {
  ctr?: number;
  avgRetention?: number;
  views24h?: number;
  totalViews?: number;
  subscribersGained?: number;
  comments?: number;
}): { positive: string[]; negative: string[] } {
  const positive: string[] = [];
  const negative: string[] = [];

  if ((metrics.ctr || 0) >= 7) positive.push("CTRが高い - サムネイル/タイトルが効果的");
  else if ((metrics.ctr || 0) < 3 && metrics.ctr !== undefined) negative.push("CTR不足 - サムネイルまたはタイトルの改善が必要");

  if ((metrics.avgRetention || 0) >= 45) positive.push("維持率が高い - 視聴者の関心を維持できている");
  else if ((metrics.avgRetention || 0) < 25 && metrics.avgRetention !== undefined) negative.push("維持率不足 - 冒頭や構成の改善が必要");

  if ((metrics.views24h || 0) >= 5000) positive.push("初動が強い - タイミングと話題性が良い");

  if ((metrics.subscribersGained || 0) >= 20) positive.push("登録者増加が多い - チャンネル成長に貢献");

  if ((metrics.comments || 0) >= 20) positive.push("コメントが活発 - 視聴者エンゲージメントが高い");

  if ((metrics.totalViews || 0) < 1000 && metrics.totalViews !== undefined) negative.push("再生数が少ない - テーマ需要またはインプレッション不足の可能性");

  return { positive, negative };
}

export function generateImprovementSuggestions(metrics: {
  ctr?: number;
  avgRetention?: number;
  totalViews?: number;
  estimatedRevenue?: number;
  totalCost: number;
}): string[] {
  const suggestions: string[] = [];

  if ((metrics.ctr || 0) < 5) {
    suggestions.push("【企画】視聴者の関心が高いテーマを選定してください");
    suggestions.push("【タイトル】具体的な数字や感情を含むタイトルに変更してください");
    suggestions.push("【サムネイル】表情やテキストのコントラストを強化してください");
  }

  if ((metrics.avgRetention || 0) < 30) {
    suggestions.push("【冒頭】最初の15秒で視聴者の関心を引く構成にしてください");
    suggestions.push("【台本】情報の優先順位を見直し、重要な内容を前半に配置してください");
  }

  if ((metrics.totalViews || 0) < 3000) {
    suggestions.push("【投稿時間】ターゲット視聴者(65歳以上女性)の活動時間帯に合わせてください");
  }

  if (metrics.totalCost > 0 && (metrics.estimatedRevenue || 0) < metrics.totalCost * 0.5) {
    suggestions.push("【企画】費用対効果の高い企画テーマを優先してください");
  }

  return suggestions;
}
