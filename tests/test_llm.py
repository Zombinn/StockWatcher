"""测试 LLM 模块"""
from src.llm.interpreter import LLMAnalysis, _LLM_ANALYSIS_SYSTEM_PROMPT, _NEWS_ANALYSIS_PROMPT
from src.llm.client import OpenAICompatibleClient


def test_llm_analysis_dataclass():
    """测试 LLM 分析结果结构"""
    a = LLMAnalysis(summary="测试结论", trend_analysis="趋势向上", technical_insight="MACD金叉", score_adjustment=5.0)
    assert a.summary == "测试结论"
    assert a.trend_analysis == "趋势向上"
    assert a.score_adjustment == 5.0
    assert a.risk_warning == ""


def test_llm_prompts_exist():
    """测试 LLM Prompt 存在"""
    assert len(_LLM_ANALYSIS_SYSTEM_PROMPT) > 100
    assert len(_NEWS_ANALYSIS_PROMPT) > 50


def test_parse_llm_response():
    """测试 LLM JSON 解析"""
    from src.llm.interpreter import LLMInterpreter
    interpreter = LLMInterpreter(client=None)

    # 模拟 LLM 返回的 JSON
    response = '{"summary": "看涨", "trend_analysis": "趋势向上", "technical_insight": "MACD金叉", "risk_warning": "", "operation_advice": "买入", "score_adjustment": 10, "key_levels": {"support": 150, "resistance": 160}}'
    result = interpreter._parse_llm_response(response)
    assert result is not None
    assert result.summary == "看涨"
    assert result.trend_analysis == "趋势向上"
    assert result.score_adjustment == 10.0
    assert result.key_levels["support"] == 150.0
