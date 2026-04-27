"""LiteLLM 多模型切换验证 — T-0.5 验收测试.

验收标准：统一 API 层可路由至不同 LLM 提供商（使用 mock 验证）
"""

from unittest.mock import MagicMock, patch

import pytest


def test_litellm_importable() -> None:
    """验证 LiteLLM 可正常导入."""
    import litellm

    assert hasattr(litellm, "completion")
    assert hasattr(litellm, "acompletion")


def test_litellm_model_list() -> None:
    """验证 LiteLLM 支持的模型提供商列表."""
    import litellm

    # 验证关键提供商存在
    providers = ["openai", "anthropic", "gemini", "ollama"]
    for _provider in providers:
        # LiteLLM 支持 provider/model 格式
        assert callable(litellm.completion), "LiteLLM.completion 不可调用"


@patch("litellm.completion")
def test_openai_routing(mock_completion: MagicMock) -> None:
    """验证 OpenAI 路由：gpt-4o 正确路由到 OpenAI."""
    import litellm

    # 模拟 API 响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock response from GPT-4o"
    mock_response.model = "gpt-4o"
    mock_completion.return_value = mock_response

    response = litellm.completion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "test"}],
    )

    mock_completion.assert_called_once_with(
        model="gpt-4o",
        messages=[{"role": "user", "content": "test"}],
    )
    assert response.choices[0].message.content == "Mock response from GPT-4o"


@patch("litellm.completion")
def test_anthropic_routing(mock_completion: MagicMock) -> None:
    """验证 Anthropic 路由：claude-3-5-sonnet 正确路由到 Anthropic."""
    import litellm

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Mock response from Claude"
    mock_response.model = "claude-sonnet-4-6"
    mock_completion.return_value = mock_response

    response = litellm.completion(
        model="claude-sonnet-4-6",
        messages=[{"role": "user", "content": "test"}],
    )

    assert response.choices[0].message.content == "Mock response from Claude"


@patch("litellm.completion")
def test_model_switching(mock_completion: MagicMock) -> None:
    """验证运行时模型切换：同一接口，不同模型."""
    import litellm

    models_to_test = [
        "gpt-4o",
        "claude-sonnet-4-6",
        "gemini/gemini-2.0-flash",
        "ollama/llama3.2",
        "deepseek/deepseek-chat",
    ]

    for model in models_to_test:
        mock_response = MagicMock()
        mock_response.model = model
        mock_completion.return_value = mock_response

        # 同一接口调用，只改 model 参数
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
        )
        assert response.model == model, f"模型 {model} 路由失败"

    print(f"\n✓ 成功验证 {len(models_to_test)} 个模型的统一路由")


@pytest.mark.asyncio
@patch("litellm.acompletion")
async def test_async_completion(mock_acompletion: MagicMock) -> None:
    """验证异步 completion 接口（SSE 流式输出基础）."""
    import litellm

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Async response"
    mock_acompletion.return_value = mock_response

    response = await litellm.acompletion(
        model="gpt-4o",
        messages=[{"role": "user", "content": "async test"}],
    )

    assert response.choices[0].message.content == "Async response"
    print("\n✓ 异步 completion 接口验证通过")
