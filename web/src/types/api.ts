export interface ApiResponse<T = any> {
  success: boolean;
  [key: string]: any;
}

export interface AnalysisResult {
  code: string;
  name: string;
  price: number;
  change_pct: number;
  score: number;
  trend: string;
  signal: string;
  risk: string;
  suggestion: string;
  support: number;
  resistance: number;
  indicators: {
    ma5: number; ma10: number; ma20: number;
    macd: number; macd_hist: number;
    rsi_14: number;
    boll_up: number; boll_low: number;
  };
}

export interface PortfolioData {
  total_cost: number;
  total_market_value: number;
  total_profit: number;
  total_profit_pct: number;
  risk_score: number;
  suggestion: string;
  positions: Position[];
}

export interface Position {
  code: string; name: string; quantity: number;
  cost_price: number; current_price: number;
  market_value: number; profit_pct: number;
  profit_amount: number; weight: number;
}

export interface IndexData {
  name: string; price: number; change_pct: number;
}

export interface SectorData {
  name: string; change_pct: number;
}

export interface AlertRule {
  id: string; code: string; name: string;
  rule_type: string; threshold: number; enabled: boolean;
}

export interface AlertEvent {
  rule_id: string; message: string; timestamp: string;
}

export interface BacktestData {
  initial_capital: number; final_value: number;
  total_return: number; total_return_pct: number;
  annual_return: number; max_drawdown: number;
  win_rate: number; total_trades: number;
  sharpe_ratio: number; start_date: string; end_date: string;
  trades: TradeRecord[];
}

export interface TradeRecord {
  date: string; action: string; price: number;
  shares: number; amount: number; reason: string;
}

export interface ConfigSection {
  key: string; label: string; fields: ConfigField[];
}

export interface ConfigField {
  key: string; label: string; type: string;
  default: any; description: string; value?: string;
  options?: string[]; secret?: boolean;
}
