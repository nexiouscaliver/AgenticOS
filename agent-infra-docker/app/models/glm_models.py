"""
GLM (ChatGLM) model provider - Good for multilingual content
"""

import os
from typing import Optional
from agno.models.openai import OpenAIChat


def create_glm_model(
    model_id: str = "glm-4",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> OpenAIChat:
    """
    Create GLM model - Excellent for Chinese/multilingual content
    
    GLM uses OpenAI-compatible API with Zhipu AI base URL
    Cost: ~0.00020/1K tokens
    
    Supported models:
    - glm-4: Latest GLM-4 model
    - glm-4-air: Faster, lighter version
    - glm-4-airx: Extended context version
    - glm-4-flash: Fastest response time
    
    Args:
        model_id: GLM model identifier
        temperature: Response randomness (0.0-2.0)
        max_tokens: Maximum response tokens
        **kwargs: Additional model parameters
        
    Returns:
        Configured GLM model instance
    """
    
    # Validate API key
    api_key = os.getenv("GLM_API_KEY")
    if not api_key:
        raise ValueError("GLM_API_KEY environment variable is required")
    
    # GLM model configurations
    model_configs = {
        "glm-4": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00020,
            "context_window": 128000,
        },
        "glm-4-air": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00015,
            "context_window": 128000,
        },
        "glm-4-airx": {
            "temperature": temperature,
            "max_tokens": max_tokens or 8192,
            "cost_per_1k_tokens": 0.00025,
            "context_window": 256000,
        },
        "glm-4-flash": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00010,
            "context_window": 128000,
        }
    }
    
    # Get model configuration
    config = model_configs.get(model_id, model_configs["glm-4"])
    
    return OpenAIChat(
        id=model_id,
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/",
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        **kwargs
    )


def get_glm_cost_per_token(model_id: str) -> float:
    """Get cost per 1K tokens for GLM models"""
    costs = {
        "glm-4": 0.00020,
        "glm-4-air": 0.00015,
        "glm-4-airx": 0.00025,
        "glm-4-flash": 0.00010,
    }
    return costs.get(model_id, 0.00020)


def get_cheapest_glm_model() -> str:
    """Get the most cost-effective GLM model"""
    return "glm-4-flash"


def get_best_glm_model_for_task(task_type: str) -> str:
    """
    Select optimal GLM model based on task requirements
    
    Args:
        task_type: Type of task (research, creative, analysis, multilingual)
        
    Returns:
        Recommended model ID
    """
    task_models = {
        "research": "glm-4",
        "creative": "glm-4",
        "analysis": "glm-4-air",
        "multilingual": "glm-4",
        "chinese": "glm-4",
        "fast": "glm-4-flash",
        "speed": "glm-4-flash",
        "extended": "glm-4-airx",
        "long_context": "glm-4-airx",
    }
    
    return task_models.get(task_type.lower(), "glm-4")