"""
Model Factory - Intelligent model selection with cost optimization
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, Union
from agno.models.base import Model
from agno.models.google.gemini import Gemini


GEMINI_MODEL_ID = "gemini-2.5-flash-lite"


class ModelProvider(Enum):
    """Available model providers"""
    GEMINI = "gemini"


class TaskType(Enum):
    """Task types for model optimization"""
    RESEARCH = "research"
    CREATIVE = "creative"
    ANALYSIS = "analysis"
    CODING = "coding"
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTILINGUAL = "multilingual"
    FAST = "fast"


class ModelFactory:
    """Factory for creating and managing AI models with cost optimization"""

    # Model cost per 1K tokens (approximate, as of 2025)
    MODEL_COSTS = {
        "gemini-2.5-flash-lite": 0.000075,
    }

    # All task types and priorities map to gemini-2.5-flash-lite
    TASK_MODEL_MAP = {
        TaskType.RESEARCH:     {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.CREATIVE:     {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.ANALYSIS:     {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.CODING:       {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.SIMPLE:       {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.COMPLEX:      {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.MULTILINGUAL: {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
        TaskType.FAST:         {"budget": GEMINI_MODEL_ID, "balanced": GEMINI_MODEL_ID, "premium": GEMINI_MODEL_ID},
    }

    @classmethod
    def create_model(
        cls,
        model_id: str = GEMINI_MODEL_ID,
        provider: Optional[ModelProvider] = None,
        thinking_budget: int = 5000,
        **kwargs
    ) -> Model:
        """
        Create a model instance with native Gemini thinking enabled by default.

        Args:
            model_id: Model identifier (defaults to gemini-2.5-flash-lite)
            provider: Model provider (auto-detected if None)
            thinking_budget: Gemini thinking token budget (default 5000, set 0 to disable)
            **kwargs: Additional model parameters

        Returns:
            Configured model instance with thinking enabled
        """
        api_key = kwargs.pop("api_key", os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"))
        return Gemini(
            id=model_id,
            api_key=api_key,
            thinking_budget=thinking_budget,
            include_thoughts=True,
            **kwargs,
        )

    @classmethod
    def get_optimal_model(
        cls,
        task_type: Union[TaskType, str],
        priority: str = "balanced",
        max_cost_per_1k: Optional[float] = None
    ) -> str:
        """
        Get optimal model for a task with cost constraints
        
        Args:
            task_type: Type of task
            priority: "budget", "balanced", or "premium"
            max_cost_per_1k: Maximum cost per 1K tokens
            
        Returns:
            Recommended model ID
        """
        if isinstance(task_type, str):
            task_type = TaskType(task_type.lower())

        recommendations = cls.TASK_MODEL_MAP.get(task_type, cls.TASK_MODEL_MAP[TaskType.SIMPLE])
        model_id = recommendations.get(priority, recommendations["balanced"])

        if max_cost_per_1k is not None:
            model_cost = cls.MODEL_COSTS.get(model_id, 0.001)
            if model_cost > max_cost_per_1k:
                model_id = cls._find_cheapest_model(max_cost_per_1k)

        return model_id

    @classmethod
    def get_cheapest_model(cls) -> str:
        """Get the most cost-effective model available"""
        return GEMINI_MODEL_ID

    @classmethod
    def get_model_cost(cls, model_id: str) -> float:
        """Get cost per 1K tokens for a model"""
        return cls.MODEL_COSTS.get(model_id, 0.001)

    @classmethod
    def compare_models(cls, model_ids: list) -> Dict[str, Dict[str, Any]]:
        comparison = {}
        for model_id in model_ids:
            cost = cls.get_model_cost(model_id)
            comparison[model_id] = {
                "provider": ModelProvider.GEMINI.value,
                "cost_per_1k_tokens": cost,
                "cost_rank": 0,
                "suitable_for": cls._get_model_use_cases(model_id),
            }
        sorted_by_cost = sorted(comparison.items(), key=lambda x: x[1]["cost_per_1k_tokens"])
        for i, (model_id, _) in enumerate(sorted_by_cost):
            comparison[model_id]["cost_rank"] = i + 1
        return comparison

    @classmethod
    def _find_cheapest_model(cls, max_cost: float) -> str:
        affordable = [(m, c) for m, c in cls.MODEL_COSTS.items() if c <= max_cost]
        return min(affordable, key=lambda x: x[1])[0] if affordable else cls.get_cheapest_model()

    @classmethod
    def _get_model_use_cases(cls, model_id: str) -> list:
        return [
            task_type.value
            for task_type, recommendations in cls.TASK_MODEL_MAP.items()
            if model_id in recommendations.values()
        ]


# Convenience function for quick model creation
def get_optimal_model(
    task_type: Union[TaskType, str],
    priority: str = "balanced",
    max_cost_per_1k: Optional[float] = None,
    **kwargs
) -> Model:
    model_id = ModelFactory.get_optimal_model(task_type, priority, max_cost_per_1k)
    return ModelFactory.create_model(model_id, **kwargs)


# Environment-based model selection
def get_model_from_env(env_var: str = "DEFAULT_MODEL_ID", fallback: str = GEMINI_MODEL_ID) -> Model:
    """Get model from environment variable with fallback"""
    model_id = os.getenv(env_var, fallback)
    return ModelFactory.create_model(model_id)