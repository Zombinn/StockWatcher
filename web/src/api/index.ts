const BASE = '/api/v1';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await res.json();
  if (!data.success) throw new Error(data.error || data.message || '请求失败');
  return data;
}

export const api = {
  // 分析
  analyze: () => request<any>('/analyze'),
  analyzeStock: (code: string) => request<any>(`/stocks/${code}`),
  analyzeWithLLM: (code: string) => request<any>(`/analyze/llm/${code}`),

  // 大盘
  marketReview: (market = "cn") => request<any>(`/market/review?market=${market}`),
  economicCalendar: (days = 90) => request<any>(`/market/economic-calendar?days=${days}`),

  // 持仓
  getPortfolio: () => request<any>('/portfolio'),
  addPosition: (code: string, quantity: number, cost_price: number, name?: string, market?: string) =>
    request<any>(`/portfolio/positions?code=${code}&quantity=${quantity}&cost_price=${cost_price}&name=${name || ''}${market ? `&market=${market}` : ''}`, { method: 'POST' }),
  removePosition: (code: string, quantity?: number) =>
    request<any>(`/portfolio/positions/${code}${quantity ? `?quantity=${quantity}` : ''}`, { method: 'DELETE' }),
  importPositions: (text: string) =>
    request<any>('/portfolio/import', { method: 'POST', body: JSON.stringify({ text }) }),

  // TimesFM 价格预测
  stockForecast: (code: string, horizon = 14) =>
    request<any>(`/stocks/${encodeURIComponent(code)}/forecast?horizon=${horizon}`),

  // K 线数据
  stockKline: (code: string, count = 60) =>
    request<any>(`/stocks/${encodeURIComponent(code)}/kline?count=${count}`),

  // 选股筛选（真实行情 + 技术分析）
  screenStocks: (market: string, strategy: string, limit = 12) =>
    request<any>(`/screen?market=${market}&strategy=${encodeURIComponent(strategy)}&limit=${limit}`),

  // 代码下拉（自选 + 持仓去重）
  getSymbols: () => request<any>('/symbols'),

  // 自选股
  getWatchlist: () => request<any>('/watchlist'),
  addWatchlist: (code: string) => request<any>(`/watchlist?code=${encodeURIComponent(code)}`, { method: 'POST' }),
  removeWatchlist: (code: string) => request<any>(`/watchlist/${encodeURIComponent(code)}`, { method: 'DELETE' }),

  // 资讯 / 交易日
  stockNews: (code: string, limit = 10) => request<any>(`/stocks/${code}/news?limit=${limit}`),
  tradingDay: (date?: string) => request<any>(`/market/trading-day${date ? `?date=${date}` : ''}`),

  // 告警
  getAlerts: () => request<any>('/alerts'),
  addAlert: (code: string, rule_type: string, threshold: number, name?: string) =>
    request<any>(`/alerts/rules?code=${code}&rule_type=${rule_type}&threshold=${threshold}&name=${name || ''}`, { method: 'POST' }),
  removeAlert: (ruleId: string) =>
    request<any>(`/alerts/rules/${ruleId}`, { method: 'DELETE' }),
  checkAlerts: () => request<any>('/alerts/check', { method: 'POST', body: '{}' }),

  // Agent
  getStrategies: () => request<any>('/agent/strategies'),
  createSession: (code: string, name?: string) =>
    request<any>(`/agent/session?code=${code}&name=${name || ''}`, { method: 'POST' }),
  agentChat: (sessionId: string, message: string, strategy?: string) =>
    request<any>(`/agent/chat?session_id=${sessionId}&message=${encodeURIComponent(message)}${strategy ? `&strategy=${strategy}` : ''}`, { method: 'POST' }),

  // 回测
  backtest: (code: string, strategy?: string, startDate?: string, endDate?: string, capital?: number, commission?: number, slippage?: number) => {
    let url = `/backtest?code=${code}&strategy=${strategy || 'ma_cross'}`;
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    if (capital) url += `&initial_capital=${capital}`;
    if (commission != null) url += `&commission_rate=${commission}`;
    if (slippage != null) url += `&slippage=${slippage}`;
    return request<any>(url);
  },

  // 配置
  getConfigSections: () => request<any>('/config/sections'),
  getConfigValues: () => request<any>('/config/values'),
  updateConfig: (updates: Record<string, string>) =>
    request<any>('/config/update', { method: 'POST', body: JSON.stringify({ updates }) }),
  resetConfig: () => request<any>('/config/reset', { method: 'POST', body: '{}' }),
  // 报告
  listReports: (page = 1, pageSize = 10) => request<any>(`/reports?page=${page}&page_size=${pageSize}`),
  getReport: (rid: string) => request<any>(`/reports/${rid}`),
  deleteReport: (rid: string) => request<any>(`/reports/${rid}`, { method: 'DELETE' }),
  deleteReportsBatch: (ids: string[]) => request<any>('/reports/delete', { method: 'POST', body: JSON.stringify({ ids }) }),
  // 形态识别
  stockPatterns: (code: string) => request<any>(`/stocks/${encodeURIComponent(code)}/patterns`),
  // 财报日历
  stockEarnings: (code: string) => request<any>(`/stocks/${encodeURIComponent(code)}/earnings`),
  // 回测报告
  backtestReport: (code: string, strategy: string, format = 'markdown', startDate?: string, endDate?: string) =>
    request<any>('/backtest/report', {
      method: 'POST',
      body: JSON.stringify({ code, strategy, format, start_date: startDate, end_date: endDate }),
    }),
  saveBacktestReport: (code: string, content: string, format = 'markdown') =>
    request<any>('/backtest/report/save', {
      method: 'POST',
      body: JSON.stringify({ code, content, format }),
    }),
};
