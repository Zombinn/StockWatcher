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
  marketReview: () => request<any>('/market/review'),

  // 持仓
  getPortfolio: () => request<any>('/portfolio'),
  addPosition: (code: string, quantity: number, cost_price: number, name?: string, market?: string) =>
    request<any>(`/portfolio/positions?code=${code}&quantity=${quantity}&cost_price=${cost_price}&name=${name || ''}${market ? `&market=${market}` : ''}`, { method: 'POST' }),
  removePosition: (code: string, quantity?: number) =>
    request<any>(`/portfolio/positions/${code}${quantity ? `?quantity=${quantity}` : ''}`, { method: 'DELETE' }),
  importPositions: (text: string) =>
    request<any>('/portfolio/import', { method: 'POST', body: JSON.stringify({ text }) }),

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
  backtest: (code: string, strategy?: string, startDate?: string, endDate?: string) =>
    request<any>(`/backtest?code=${code}&strategy=${strategy || 'ma_cross'}${startDate ? `&start_date=${startDate}` : ''}${endDate ? `&end_date=${endDate}` : ''}`),

  // 配置
  getConfigSections: () => request<any>('/config/sections'),
  getConfigValues: () => request<any>('/config/values'),
  updateConfig: (updates: Record<string, string>) =>
    request<any>('/config/update', { method: 'POST', body: JSON.stringify({ updates }) }),
  resetConfig: () => request<any>('/config/reset', { method: 'POST', body: '{}' }),
};
