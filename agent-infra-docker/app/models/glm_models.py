"""
GLM (ChatGLM) model provider - Good for multilingual content
"""

import os
from typing import Optional
from .glm45_provider import GLM45Provider


def create_glm_model(
    model_id: str = "glm-4.5-air",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> GLM45Provider:
    """
    Create GLM model - Excellent for Chinese/multilingual content
    
    GLM uses OpenAI-compatible API with Zhipu/Z.ai base URL
    Cost: ~0.00020/1K tokens
    
    Supported models:
    - glm-4.5-air: Faster, lighter version
    - glm-4.5-air-fast: Local fast model
    
    Args:
        model_id: GLM model identifier
        temperature: Response randomness (0.0-2.0)
        max_tokens: Maximum response tokens
        **kwargs: Additional model parameters
        
    Returns:
        Configured GLM model instance
    """
    
    # Determine API key and Base URL based on model
    if model_id == "glm-4.5-air-fast":
        api_key = os.getenv("GLM_FAST_API_KEY", "dummy")
        base_url = os.getenv("GLM_FAST_BASE_URL", "http://8.213.81.97:8005/v1")
    else:
        # Default to local GLM for other GLM models
        api_key = os.getenv("GLM_API_KEY_LOCAL", "dummy")
        base_url = os.getenv("GLM_URL_LOCAL", "http://8.213.81.97:8000/v1")

    # Fallback to standard GLM_API_KEY if local ones aren't set (though user said to use local)
    if not api_key or api_key == "dummy":
         # Check if we have the standard key, otherwise keep dummy if it's local
         standard_key = os.getenv("GLM_API_KEY")
         if standard_key:
             api_key = standard_key
             # If using standard key, maybe we should use standard URL? 
             # But user explicitly asked to use local. 
             # I will respect the user's provided values as defaults.
    
    # GLM model configurations (only supported IDs)
    model_configs = {
        "glm-4.5-air": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00015,
            "context_window": 128000,
        },
        "glm-4.5-air-fast": {
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
            "cost_per_1k_tokens": 0.00015,
            "context_window": 32000, # Based on GLM_FAST_SAFE_OUTPUT_LIMIT? No that's output.
        },
    }
    
    # Get model configuration (default to glm-4.5-air)
    config = model_configs.get(model_id, model_configs["glm-4.5-air"])
    
    return GLM45Provider(
        id=model_id,
        api_key=api_key,
        base_url=kwargs.pop("base_url", base_url),
        temperature=config["temperature"],
        max_tokens=config["max_tokens"],
        **kwargs
    )


def get_glm_cost_per_token(model_id: str) -> float:
    """Get cost per 1K tokens for GLM models"""
    costs = {
        "glm-4.5-air": 0.00020,
        "glm-4.5-air-fast": 0.00015,
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
        "research": "glm-4.5-air",
        "creative": "glm-4.5-air",
        "analysis": "glm-4.5-air",
        "multilingual": "glm-4.5-air",
        "chinese": "glm-4.5-air",
        "fast": "glm-4.5-air-fast",
        "speed": "glm-4.5-air-fast",
        "extended": "glm-4.5-air",
        "long_context": "glm-4.5-air",
    }
    
    return task_models.get(task_type.lower(), "glm-4.5-air")