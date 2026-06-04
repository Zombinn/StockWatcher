/** 分析报告类型定义 */

export interface ReportMeta {
  stockCode: string;
  stockName: string;
  currentPrice?: number;
  changePct?: number;
  reportType: 'analysis' | 'market_review';
  createdAt: string;
}

export interface ReportStrategy {
  idealBuy?: string;
  secondaryBuy?: string;
  stopLoss?: string;
  takeProfit?: string;
}

export interface ReportSummary {
  analysisSummary: string;
  operationAdvice: string;
  trendPrediction: string;
  sentimentScore: number;
}

export interface AnalysisReport {
  meta: ReportMeta;
  summary: ReportSummary;
  strategy?: ReportStrategy;
}

export interface ScreeningCandidate {
  code: string;
  name: string;
  score: number;
  price?: number;
  changePct?: number;
  reason: string;
  signal?: string;
}
