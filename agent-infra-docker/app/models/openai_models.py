"""
OpenAI model provider with cost optimization support
"""

import os
from typing import Optional
from agno.models.openai import OpenAIChat


def create_openai_model(
    model_id: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> OpenAIChat:
    """
    Create OpenAI model with cost optimization
    
    Supported models:
    - gpt-4o-mini: Most cost-effective option (0.00015/1K tokens)
    - gpt-4o: Higher capability, higher cost
    - gpt-3.5-turbo: Legacy option
    
    Args:
        model_id: OpenAI model identifier
        temperature: Response randomness (0.0-2.0)
        max_tokens: Maximum response tokens
        **kwargs: Additional model parameters
        
    Returns:
        Configured OpenAI model instance
    """
    
    # Validate API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    # Cost-optimized model configurations
    model_configs = {
        "gpt-4o-mini": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00015,
        },
        "gpt-4o": {
            "temperature": temperature,
            "max_tokens": max_tokens or 8192,
            "cost_per_1k_tokens": 0.00300,
        },
        "gpt-3.5-turbo": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00050,
        }
    }
    
    # Get model configuration
    config = model_configs.get(model_id, model_configs["gpt-4o-mini"])
    
    return OpenAIChat(
        id=model_id,
        api_key=api_key,
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        **kwargs
    )


def get_openai_cost_per_token(model_id: str) -> float:
    """Get cost per 1K tokens for OpenAI models"""
    costs = {
        "gpt-4o-mini": 0.00015,
        "gpt-4o": 0.00300,
        "gpt-3.5-turbo": 0.00050,
    }
    return costs.get(model_id, 0.00015)


def get_cheapest_openai_model() -> str:
    """Get the most cost-effective OpenAI model"""
    return "gpt-4o-mini"


def get_best_openai_model_for_task(task_type: str) -> str:
    """
    Select optimal OpenAI model based on task requirements
    
    Args:
        task_type: Type of task (research, creative, analysis, simple)
        
    Returns:
        Recommended model ID
    """
    task_models = {
        "research": "gpt-4o-mini",      # Good balance for research
        "creative": "gpt-4o",           # Better for creative tasks
        "analysis": "gpt-4o-mini",      # Cost-effective for analysis
        "simple": "gpt-4o-mini",        # Cheapest for simple tasks
        "complex": "gpt-4o",            # Higher capability needed
    }
    
    return task_models.get(task_type.lower(), "gpt-4o-mini")