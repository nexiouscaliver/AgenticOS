"""
Model Factory - Intelligent model selection with cost optimization
"""

import os
from enum import Enum
from typing import Dict, Any, Optional, Union
from agno.models.base import Model
from .glm_models import (
    create_glm_model,
    get_glm_cost_per_token,
    get_best_glm_model_for_task
)



class ModelProvider(Enum):
    """Available model providers"""
    GLM = "glm"


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
    
    # Model cost per 1K tokens (approximate)
    MODEL_COSTS = {
        # GLM models (supported only)
        "glm-4.5-air": 0.00020,
        "glm-4.5-air-fast": 0.00015,
    }
    
    # Task-specific model recommendations
    TASK_MODEL_MAP = {
        TaskType.RESEARCH: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air", 
            "premium": "glm-4.5-air"
        },
        TaskType.CREATIVE: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air",
            "premium": "glm-4.5-air"
        },
        TaskType.ANALYSIS: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air",
            "premium": "glm-4.5-air"
        },
        TaskType.CODING: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air",
            "premium": "glm-4.5-air"
        },
        TaskType.SIMPLE: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air-fast",
            "premium": "glm-4.5-air"
        },
        TaskType.COMPLEX: {
            "budget": "glm-4.5-air",
            "balanced": "glm-4.5-air",
            "premium": "glm-4.5-air"
        },
        TaskType.MULTILINGUAL: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air",
            "premium": "glm-4.5-air"
        },
        TaskType.FAST: {
            "budget": "glm-4.5-air-fast",
            "balanced": "glm-4.5-air-fast",
            "premium": "glm-4.5-air"
        }
    }
    
    @classmethod
    def create_model(
        self,
        model_id: str,
        provider: Optional[ModelProvider] = None,
        **kwargs
    ) -> Model:
        """
        Create a model instance
        
        Args:
            model_id: Model identifier
            provider: Model provider (auto-detected if None)
            **kwargs: Additional model parameters
            
        Returns:
            Configured model instance
        """
        # Auto-detect provider if not specified
        if provider is None:
            provider = self._detect_provider(model_id)
        
        if provider == ModelProvider.GLM:
            return create_glm_model(model_id, **kwargs)
        else:
            # Default to GLM
            return create_glm_model(model_id, **kwargs)
    
    @classmethod
    def get_optimal_model(
        self,
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
        
        # Get task-specific recommendations
        recommendations = self.TASK_MODEL_MAP.get(task_type, self.TASK_MODEL_MAP[TaskType.SIMPLE])
        model_id = recommendations.get(priority, recommendations["balanced"])
        
        # Apply cost constraint
        if max_cost_per_1k is not None:
            model_cost = self.MODEL_COSTS.get(model_id, 0.001)
            if model_cost > max_cost_per_1k:
                # Find cheapest model that meets constraint
                model_id = self._find_cheapest_model(max_cost_per_1k)
        
        return model_id
    
    @classmethod
    def get_cheapest_model(self) -> str:
        """Get the most cost-effective model available"""
        return "glm-4.5-air-fast"  # Currently cheapest at $0.00014/1K tokens
    
    @classmethod
    def get_model_cost(self, model_id: str) -> float:
        """Get cost per 1K tokens for a model"""
        return self.MODEL_COSTS.get(model_id, 0.001)  # Default to $0.001 if unknown
    
    @classmethod
    def compare_models(self, model_ids: list) -> Dict[str, Dict[str, Any]]:
        """
        Compare multiple models by cost and capabilities
        
        Args:
            model_ids: List of model IDs to compare
            
        Returns:
            Comparison data for each model
        """
        comparison = {}
        
        for model_id in model_ids:
            provider = self._detect_provider(model_id)
            cost = self.get_model_cost(model_id)
            
            comparison[model_id] = {
                "provider": provider.value,
                "cost_per_1k_tokens": cost,
                "cost_rank": 0,  # Will be filled below
                "suitable_for": self._get_model_use_cases(model_id)
            }
        
        # Add cost rankings
        sorted_by_cost = sorted(comparison.items(), key=lambda x: x[1]["cost_per_1k_tokens"])
        for i, (model_id, data) in enumerate(sorted_by_cost):
            comparison[model_id]["cost_rank"] = i + 1
        
        return comparison
    
    @classmethod
    def _detect_provider(self, model_id: str) -> ModelProvider:
        """Auto-detect provider from model ID"""
        if model_id.startswith("glm"):
            return ModelProvider.GLM
        else:
            return ModelProvider.GLM
    

    
    @classmethod
    def _find_cheapest_model(self, max_cost: float) -> str:
        """Find cheapest model under cost constraint"""
        affordable_models = [
            (model_id, cost) for model_id, cost in self.MODEL_COSTS.items()
            if cost <= max_cost
        ]
        
        if not affordable_models:
            return self.get_cheapest_model()
        
        return min(affordable_models, key=lambda x: x[1])[0]
    
    @classmethod
    def _get_model_use_cases(self, model_id: str) -> list:
        """Get recommended use cases for a model"""
        use_cases = []
        
        for task_type, recommendations in self.TASK_MODEL_MAP.items():
            if model_id in recommendations.values():
                use_cases.append(task_type.value)
        
        return use_cases


# Convenience function for quick model creation
def get_optimal_model(
    task_type: Union[TaskType, str],
    priority: str = "balanced",
    max_cost_per_1k: Optional[float] = None,
    **kwargs
) -> Model:
    """
    Get optimal model instance for a task
    
    Args:
        task_type: Type of task
        priority: "budget", "balanced", or "premium"
        max_cost_per_1k: Maximum cost per 1K tokens
        **kwargs: Additional model parameters
        
    Returns:
        Configured optimal model instance
    """
    model_id = ModelFactory.get_optimal_model(task_type, priority, max_cost_per_1k)
    return ModelFactory.create_model(model_id, **kwargs)


# Environment-based model selection
def get_model_from_env(env_var: str = "DEFAULT_MODEL_ID", fallback: str = "glm-4.5-air-fast") -> Model:
    """Get model from environment variable with fallback"""
    model_id = os.getenv(env_var, fallback)
    return ModelFactory.create_model(model_id)