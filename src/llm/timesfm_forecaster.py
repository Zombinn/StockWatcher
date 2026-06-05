"""TimesFM 时间序列预测（google-research/timesfm v2.0，Python 3.12 兼容）

模型在首次调用时从 HuggingFace 下载（~800MB），之后本地缓存。
推理在单一工作线程中运行，避免与 akshare V8 竞争。
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# TODO: 若 Google 发布 timesfm 3.x+ 且与本接口兼容，仅需更换此常量
_MODEL_REPO = "google/timesfm-2.5-200m-pytorch"   # timesfm v2.0 对应 2.5 权重
_CONTEXT_LEN = 512   # 模型最大上下文长度

_model = None          # 单例，进程内只加载一次
_model_loading = False


@dataclass
class ForecastResult:
    """预测结果"""
    dates: List[str]          # 未来日期（YYYY-MM-DD）
    forecast: List[float]     # 点预测
    lower_90: List[float]     # 90% 置信下界
    upper_90: List[float]     # 90% 置信上界
    lower_80: List[float]
    upper_80: List[float]
    last_price: float         # 最后已知价格（用于连接历史线）
    last_date: str
    model: str = "TimesFM-2.5-200M-PyTorch"


def _load_model():
    """同步加载模型（在 blocking 工作线程中调用，进程内单例）"""
    global _model, _model_loading
    if _model is not None:
        return _model
    _model_loading = True
    try:
        import timesfm
        from timesfm import configs
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file

        logger.info("正在加载 TimesFM 2.5 模型（首次从 HuggingFace 下载 ~880MB）...")
        tfm = timesfm.TimesFM_2p5_200M_torch(torch_compile=False)
        weights_path = hf_hub_download(repo_id=_MODEL_REPO, filename="model.safetensors")
        state_dict = load_file(weights_path)
        tfm.model.load_state_dict(state_dict, strict=False)
        tfm.model.eval()
        # compile 设置预测参数
        fc = configs.ForecastConfig(
            max_context=_CONTEXT_LEN,
            max_horizon=64,
            normalize_inputs=True,
            per_core_batch_size=8,
        )
        tfm.compile(fc)
        _model = tfm
        logger.info("TimesFM 2.5 模型就绪")
        return tfm
    except Exception as e:
        logger.error("TimesFM 模型加载失败: %s", e)
        raise
    finally:
        _model_loading = False


def _predict_sync(closes: np.ndarray, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """同步推理（在工作线程中调用）"""
    model = _load_model()
    valid = closes[~np.isnan(closes)]
    if len(valid) > _CONTEXT_LEN:
        valid = valid[-_CONTEXT_LEN:]
    point, quantiles = model.forecast(horizon=horizon, inputs=[valid])
    # quantiles: (1, horizon, n_quantiles)
    q = np.array(quantiles)
    return point[0], q[0] if q.ndim == 3 else q  # (horizon,), (horizon, n_quantiles)


def _future_dates(last_date_str: str, horizon: int) -> List[str]:
    """生成未来交易日日期（简化：连续日历日，跳过周末）"""
    from datetime import datetime, timedelta
    dt = datetime.strptime(last_date_str, "%Y-%m-%d")
    dates = []
    while len(dates) < horizon:
        dt += timedelta(days=1)
        if dt.weekday() < 5:   # 跳过周末
            dates.append(dt.strftime("%Y-%m-%d"))
    return dates


async def forecast(klines, horizon: int = 14) -> Optional[ForecastResult]:
    """异步入口：输入 K 线列表，输出预测结果"""
    if not klines or len(klines) < 30:
        logger.warning("K 线数量不足（%d），跳过预测", len(klines))
        return None

    closes = np.array([k.close for k in klines], dtype=np.float32)
    last_date = klines[-1].date
    last_price = float(closes[-1]) if not np.isnan(closes[-1]) else 0.0

    try:
        from src.utils.blocking import run_blocking
        point, quantiles = await run_blocking(_predict_sync, closes, horizon)
    except Exception as e:
        logger.error("TimesFM 推理失败: %s", e)
        return None

    # quantiles shape: (horizon, n_quantiles)
    # TimesFM 2.5 默认分位数: [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    # 若只有点预测则用 ±5% 作为兜底置信区间
    # quantiles[:,i]: i=0→p10, i=1→p20, …, i=8→p90
    def _q(col: int, fallback_pct: float) -> List[float]:
        if quantiles.ndim == 2 and quantiles.shape[1] > col:
            return [round(float(v), 4) for v in quantiles[:, col]]
        return [round(float(p) * fallback_pct, 4) for p in point]

    return ForecastResult(
        dates=_future_dates(last_date, horizon),
        forecast=[round(float(v), 4) for v in point],
        lower_90=_q(0, 0.95),   # p10 → 90% 区间下界
        upper_90=_q(8, 1.05),   # p90 → 90% 区间上界
        lower_80=_q(1, 0.96),   # p20 → 80% 区间下界
        upper_80=_q(7, 1.04),   # p80 → 80% 区间上界
        last_price=last_price,
        last_date=last_date,
    )
