"""
DeepSeek model provider - Most cost-effective option
"""

import os
from typing import Optional

from agno.models.openai import OpenAIChat


def create_deepseek_model(
    model_id: str = "deepseek-chat", temperature: float = 0.7, max_tokens: Optional[int] = None, **kwargs
) -> OpenAIChat:
    """
    Create DeepSeek model - cheapest option available

    DeepSeek uses OpenAI-compatible API but with different base URL
    Cost: ~0.00014/1K tokens (cheapest available)

    Supported models:
    - deepseek-chat: Main chat model
    - deepseek-coder: Code-specialized model

    Args:
        model_id: DeepSeek model identifier
        temperature: Response randomness (0.0-2.0)
        max_tokens: Maximum response tokens
        **kwargs: Additional model parameters

    Returns:
        Configured DeepSeek model instance
    """

    # Validate API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY environment variable is required")

    # DeepSeek model configurations
    model_configs = {
        "deepseek-chat": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00014,
        },
        "deepseek-coder": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00014,
        },
    }

    # Get model configuration
    config = model_configs.get(model_id, model_configs["deepseek-chat"])

    return OpenAIChat(
        id=model_id,
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        **kwargs,
    )


def get_deepseek_cost_per_token(model_id: str) -> float:
    """Get cost per 1K tokens for DeepSeek models"""
    costs = {
        "deepseek-chat": 0.00014,
        "deepseek-coder": 0.00014,
    }
    return costs.get(model_id, 0.00014)


def get_cheapest_deepseek_model() -> str:
    """Get the most cost-effective DeepSeek model"""
    return "deepseek-chat"


def get_best_deepseek_model_for_task(task_type: str) -> str:
    """
    Select optimal DeepSeek model based on task requirements

    Args:
        task_type: Type of task (research, creative, analysis, coding)

    Returns:
        Recommended model ID
    """
    task_models = {
        "research": "deepseek-chat",
        "creative": "deepseek-chat",
        "analysis": "deepseek-chat",
        "coding": "deepseek-coder",
        "development": "deepseek-coder",
        "programming": "deepseek-coder",
    }

    return task_models.get(task_type.lower(), "deepseek-chat")
