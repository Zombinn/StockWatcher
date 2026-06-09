/** 共用常量，避免各页面重复定义 */

export const MARKET_OPTIONS = [
  { value: 'cn', label: '🇨🇳 A股' },
  { value: 'hk', label: '🇭🇰 港股' },
  { value: 'us', label: '🇺🇸 美股' },
];

export const SIGNAL_COLOR: Record<string, string> = {
  强烈买入: '#e53935',
  买入: '#f5642a',
  持有: '#1e88e5',
  观望: '#94a3b8',
  卖出: '#43a047',
  强烈卖出: '#2e7d32',
};
