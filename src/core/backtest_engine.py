"""回测引擎 - 策略历史回测"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from src.data_provider.base import KLine
from src.data_provider.factory import get_provider_for_code
from src.stock_analyzer import StockAnalyzer, TechnicalIndicators

logger = logging.getLogger(__name__)


@dataclass
class TradeRecord:
    """交易记录"""
    date: str
    action: str  # buy / sell
    price: float
    shares: int
    amount: float
    reason: str = ""
    commission: float = 0.0


@dataclass
class BacktestResult:
    """回测结果"""
    code: str
    name: str = ""
    initial_capital: float = 100000.0
    commission_rate: float = 0.0003  # 佣金费率
    slippage: float = 0.001  # 滑点比例
    final_value: float = 100000.0
    total_return: float = 0.0
    total_return_pct: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    sharpe_ratio: float = 0.0
    trades: List[TradeRecord] = field(default_factory=list)
    equity_curve: List[float] = field(default_factory=list)
    start_date: str = ""
    end_date: str = ""


class BacktestEngine:
    """回测引擎 - 支持自定义策略"""

    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.0003, slippage: float = 0.001):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        self.analyzer = StockAnalyzer()

    async def run(
        self,
        code: str,
        strategy: str = "ma_cross",
        start_date: str = "",
        end_date: str = "",
    ) -> BacktestResult:
        """执行回测"""
        provider = get_provider_for_code(code)
        klines = await provider.get_kline(code, count=500)
        if not klines:
            return BacktestResult(code=code)

        # 过滤日期
        if start_date:
            klines = [k for k in klines if k.date >= start_date]
        if end_date:
            klines = [k for k in klines if k.date <= end_date]

        df = self._kline_to_df(klines)
        result = BacktestResult(
            code=code,
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage=self.slippage,
            start_date=klines[0].date if klines else "",
            end_date=klines[-1].date if klines else "",
        )

        if strategy == "ma_cross":
            result = self._strategy_ma_cross(df, result)
        elif strategy == "macd":
            result = self._strategy_macd(df, result)
        elif strategy == "rsi":
            result = self._strategy_rsi(df, result)
        elif strategy == "bollinger":
            result = self._strategy_bollinger(df, result)
        else:
            result = self._strategy_ma_cross(df, result)

        result.final_value = self.initial_capital + sum(
            t.amount for t in result.trades if t.action == "sell"
        ) - sum(t.amount for t in result.trades if t.action == "buy")

        # 计算指标
        self._compute_metrics(result, df)
        return result

    def _kline_to_df(self, klines: List[KLine]) -> pd.DataFrame:
        return pd.DataFrame([{
            "date": k.date, "open": k.open, "high": k.high,
            "low": k.low, "close": k.close, "volume": k.volume,
        } for k in klines])

    def _strategy_ma_cross(self, df: pd.DataFrame, result: BacktestResult) -> BacktestResult:
        """均线金叉死叉策略"""
        closes = df["close"].values
        ma5 = pd.Series(closes).rolling(5).mean().values
        ma20 = pd.Series(closes).rolling(20).mean().values

        cash = self.initial_capital
        shares = 0
        prev_ma5 = ma5[19] if len(ma5) > 19 else 0
        prev_ma20 = ma20[19] if len(ma20) > 19 else 0

        for i in range(20, len(df)):
            price = closes[i]
            date = df.iloc[i]["date"]

            # 金叉买入
            if prev_ma5 <= prev_ma20 and ma5[i] > ma20[i] and cash > price * 100:
                buy_shares = int(cash / price / 100) * 100
                if buy_shares > 0:
                    cost = buy_shares * price
                    cash -= cost
                    shares += buy_shares
                    result.trades.append(TradeRecord(date=date, action="buy", price=price, shares=buy_shares, amount=cost, reason="MA金叉"))

            # 死叉卖出
            elif prev_ma5 >= prev_ma20 and ma5[i] < ma20[i] and shares > 0:
                revenue = shares * price
                cash += revenue
                result.trades.append(TradeRecord(date=date, action="sell", price=price, shares=shares, amount=revenue, reason="MA死叉"))
                shares = 0

            prev_ma5, prev_ma20 = ma5[i], ma20[i]
            result.equity_curve.append(cash + shares * price)

        # 最后平仓
        if shares > 0 and len(df) > 0:
            final_price = closes[-1]
            cash += shares * final_price
            result.trades.append(TradeRecord(date=df.iloc[-1]["date"], action="sell", price=final_price, shares=shares, amount=shares * final_price, reason="平仓"))

        result.final_value = cash
        return result

    def _strategy_macd(self, df: pd.DataFrame, result: BacktestResult) -> BacktestResult:
        """MACD 金叉死叉策略"""
        closes = df["close"].values

        def ema(data, period):
            result_ema = [data[0]]
            multiplier = 2 / (period + 1)
            for val in data[1:]:
                result_ema.append((val - result_ema[-1]) * multiplier + result_ema[-1])
            return result_ema

        ema12 = ema(closes, 12)
        ema26 = ema(closes, 26)
        diffs = [e12 - e26 for e12, e26 in zip(ema12, ema26)]
        dea = ema(diffs, 9)
        macd_hist = [d - s for d, s in zip(diffs, dea)]

        cash = self.initial_capital
        shares = 0

        for i in range(35, len(df)):
            price = closes[i]
            date = df.iloc[i]["date"]

            if macd_hist[i] > 0 > macd_hist[i-1] and cash > price * 100:
                buy_shares = int(cash / price / 100) * 100
                if buy_shares > 0:
                    cash -= buy_shares * price
                    shares += buy_shares
                    result.trades.append(TradeRecord(date=date, action="buy", price=price, shares=buy_shares, amount=buy_shares * price, reason="MACD金叉"))

            elif macd_hist[i] < 0 < macd_hist[i-1] and shares > 0:
                revenue = shares * price
                cash += revenue
                result.trades.append(TradeRecord(date=date, action="sell", price=price, shares=shares, amount=revenue, reason="MACD死叉"))
                shares = 0

            result.equity_curve.append(cash + shares * price)

        if shares > 0 and len(df) > 0:
            cash += shares * closes[-1]

        result.final_value = cash
        return result

    def _strategy_rsi(self, df: pd.DataFrame, result: BacktestResult) -> BacktestResult:
        """RSI 超买超卖策略"""
        closes = df["close"].values
        rsi_values = []
        for i in range(len(closes)):
            if i < 14:
                rsi_values.append(50.0)
            else:
                gains, losses = 0, 0
                for j in range(i - 13, i + 1):
                    diff = closes[j] - closes[j - 1]
                    if diff > 0:
                        gains += diff
                    else:
                        losses -= diff
                rs = (gains / 14) / (losses / 14 + 1e-10)
                rsi_values.append(100 - 100 / (1 + rs))

        cash = self.initial_capital
        shares = 0

        for i in range(15, len(df)):
            price = closes[i]
            date = df.iloc[i]["date"]
            rsi = rsi_values[i]

            # RSI < 30 超卖买入
            if rsi < 30 and rsi_values[i-1] >= 30 and cash > price * 100:
                buy_shares = int(cash * 0.5 / price / 100) * 100
                if buy_shares > 0:
                    cash -= buy_shares * price
                    shares += buy_shares
                    result.trades.append(TradeRecord(date=date, action="buy", price=price, shares=buy_shares, amount=buy_shares * price, reason="RSI超卖"))

            # RSI > 70 超买卖出
            elif rsi > 70 and rsi_values[i-1] <= 70 and shares > 0:
                sell_shares = int(shares * 0.5 / 100) * 100
                if sell_shares > 0:
                    cash += sell_shares * price
                    shares -= sell_shares
                    result.trades.append(TradeRecord(date=date, action="sell", price=price, shares=sell_shares, amount=sell_shares * price, reason="RSI超买"))

            result.equity_curve.append(cash + shares * price)

        if shares > 0 and len(df) > 0:
            cash += shares * closes[-1]

        result.final_value = cash
        return result

    def _strategy_bollinger(self, df: pd.DataFrame, result: BacktestResult) -> BacktestResult:
        """布林带策略 - 触及下轨买入，触及上轨卖出"""
        closes = df["close"].values
        mid = pd.Series(closes).rolling(20).mean().values
        std = pd.Series(closes).rolling(20).std().values
        upper = mid + 2 * std
        lower = mid - 2 * std

        cash = self.initial_capital
        shares = 0

        for i in range(20, len(df)):
            price = closes[i]
            date = df.iloc[i]["date"]

            # 触及下轨买入
            if price <= lower[i] and cash > price * 100:
                buy_shares = int(cash * 0.3 / price / 100) * 100
                if buy_shares > 0:
                    cash -= buy_shares * price
                    shares += buy_shares
                    result.trades.append(TradeRecord(date=date, action="buy", price=price, shares=buy_shares, amount=buy_shares * price, reason="BOLL下轨"))

            # 触及上轨卖出
            elif price >= upper[i] and shares > 0:
                sell_shares = int(shares * 0.5 / 100) * 100
                if sell_shares > 0:
                    cash += sell_shares * price
                    shares -= sell_shares
                    result.trades.append(TradeRecord(date=date, action="sell", price=price, shares=sell_shares, amount=sell_shares * price, reason="BOLL上轨"))

            result.equity_curve.append(cash + shares * price)

        if shares > 0 and len(df) > 0:
            cash += shares * closes[-1]

        result.final_value = cash
        return result

    def _compute_metrics(self, result: BacktestResult, df: pd.DataFrame) -> None:
        """计算回测指标"""
        result.total_return = result.final_value - result.initial_capital
        result.total_return_pct = result.total_return / result.initial_capital * 100

        # 年化收益
        if len(df) > 1:
            days = len(df)
            years = days / 252
            if years > 0 and result.initial_capital > 0:
                result.annual_return = (result.final_value / result.initial_capital) ** (1 / years) - 1

        # 交易统计
        buys = [t for t in result.trades if t.action == "buy"]
        sells = [t for t in result.trades if t.action == "sell"]
        result.total_trades = len(buys)

        # 胜率
        for buy, sell in zip(buys, sells[:len(buys)]):
            if sell.price > buy.price:
                result.winning_trades += 1
            else:
                result.losing_trades += 1
        result.win_rate = (result.winning_trades / result.total_trades * 100) if result.total_trades > 0 else 0

        # 最大回撤
        if result.equity_curve:
            peak = result.equity_curve[0]
            for value in result.equity_curve:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak * 100
                if drawdown > result.max_drawdown:
                    result.max_drawdown = drawdown

        # 夏普比率
        if len(result.equity_curve) > 1:
            returns = np.diff(result.equity_curve) / result.equity_curve[:-1]
            if np.std(returns) > 0:
                result.sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
