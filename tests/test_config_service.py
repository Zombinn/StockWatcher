"""测试配置服务"""

from src.services.config_service import ConfigManager


def test_llm_section_has_relay_and_direct_tabs():
    """LLM 配置分组应包含中转站和非中转站 Tab 元数据"""
    sections = ConfigManager.get_sections()
    llm = next(section for section in sections if section["key"] == "llm")

    assert llm["subsections"] == [
        {"key": "relay", "label": "中转站"},
        {"key": "direct", "label": "非中转站"},
    ]

    fields = {field["key"]: field for field in llm["fields"]}
    assert fields["LLM_RELAY_ENABLED"]["subsection"] == "relay"
    assert fields["LLM_RELAY_PROVIDER"]["subsection"] == "relay"
    assert fields["LLM_RELAY_API_KEY"]["subsection"] == "relay"
    assert fields["LLM_RELAY_BASE_URL"]["subsection"] == "relay"
    assert fields["LLM_RELAY_MODEL"]["subsection"] == "relay"
    assert fields["OPENAI_API_KEY"]["subsection"] == "direct"
    assert fields["OPENAI_BASE_URL"]["subsection"] == "direct"
    assert fields["OPENAI_MODEL"]["subsection"] == "direct"
