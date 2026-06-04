"""枚举定义"""
from enum import Enum


class MarketType(str, Enum):
    A = "A"
    HK = "HK"
    US = "US"


class SignalType(str, Enum):
    BUY = "买入"
    SELL = "卖出"
    HOLD = "持有"
    WATCH = "观察"
    STRONG_BUY = "强烈买入"
    STRONG_SELL = "强烈卖出"


class DataSource(str, Enum):
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    YFINANCE = "yfinance"
    EFINANCE = "efinance"
    PYTDX = "pytdx"
    BAOSTOCK = "baostock"
    TICKFLOW = "tickflow"
    FINNHUB = "finnhub"


class NotifyChannel(str, Enum):
    WECHAT = "wechat"
    FEISHU = "feishu"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    SLACK = "slack"
    EMAIL = "email"
    PUSHPLUS = "pushplus"
    SERVERCHAN = "serverchan"
