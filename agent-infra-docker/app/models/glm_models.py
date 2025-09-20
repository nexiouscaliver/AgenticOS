"""
GLM (ChatGLM) model provider - Good for multilingual content
"""

import os
from typing import Optional
from .glm45_provider import GLM45Provider


def create_glm_model(
    model_id: str = "glm-4.5",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> GLM45Provider:
    """
    Create GLM model - Excellent for Chinese/multilingual content
    
    GLM uses OpenAI-compatible API with Zhipu/Z.ai base URL
    Cost: ~0.00020/1K tokens
    
    Supported models:
    - glm-4.5: Latest GLM-4.5 model
    - glm-4.5-air: Faster, lighter version
    
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
    
    # GLM model configurations (only supported IDs)
    model_configs = {
        "glm-4.5": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00020,
            "context_window": 128000,
        },
        "glm-4.5-air": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00015,
            "context_window": 128000,
        },
    }
    
    # Get model configuration (default to glm-4.5)
    config = model_configs.get(model_id, model_configs["glm-4.5"])
    
    return GLM45Provider(
        id=model_id,
        api_key=api_key,
        base_url=kwargs.pop("base_url", "https://api.z.ai/api/paas/v4"),
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        **kwargs
    )


def get_glm_cost_per_token(model_id: str) -> float:
    """Get cost per 1K tokens for GLM models"""
    costs = {
        "glm-4.5": 0.00020,
        "glm-4.5-air": 0.00015,
    }
    return costs.get(model_id, 0.00020)


def get_cheapest_glm_model() -> str:
    """Get the most cost-effective GLM model"""
    return "glm-4.5-air"


def get_best_glm_model_for_task(task_type: str) -> str:
    """
    Select optimal GLM model based on task requirements
    
    Args:
        task_type: Type of task (research, creative, analysis, multilingual)
        
    Returns:
        Recommended model ID
    """
    task_models = {
        "research": "glm-4.5",
        "creative": "glm-4.5",
        "analysis": "glm-4.5-air",
        "multilingual": "glm-4.5",
        "chinese": "glm-4.5",
        "fast": "glm-4.5-air",
        "speed": "glm-4.5-air",
        "extended": "glm-4.5",
        "long_context": "glm-4.5",
    }
    
    return task_models.get(task_type.lower(), "glm-4.5")