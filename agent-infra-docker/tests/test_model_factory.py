"""
Model Factory and Cost Optimization Tests
"""

import pytest
import os
from unittest.mock import patch, MagicMock

# Import our model factory
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

try:
    from app.models.factory import ModelFactory, TaskType, get_optimal_model
    from app.models.openai_models import create_openai_model, get_openai_cost_per_token
    from app.models.deepseek_models import create_deepseek_model, get_deepseek_cost_per_token
    from app.models.glm_models import create_glm_model, get_glm_cost_per_token
except ImportError:
    # If imports fail, we'll skip these tests
    pytest.skip("Model factory modules not available", allow_module_level=True)


class TestModelFactory:
    """Test model factory functionality"""
    
    def test_model_cost_tracking(self):
        """Test that model costs are properly tracked"""
        # Test cost retrieval
        openai_cost = ModelFactory.get_model_cost("gpt-4o-mini")
        deepseek_cost = ModelFactory.get_model_cost("deepseek-chat")
        glm_cost = ModelFactory.get_model_cost("glm-4.5-air")
        
        # Costs should be reasonable (between 0 and 1 dollar per 1K tokens)
        assert 0 < openai_cost < 1, "OpenAI cost should be reasonable"
        assert 0 < deepseek_cost < 1, "DeepSeek cost should be reasonable"  
        assert 0 < glm_cost < 1, "GLM cost should be reasonable"
        
        # DeepSeek should be cheapest
        assert deepseek_cost <= openai_cost, "DeepSeek should be cost-effective"
        assert deepseek_cost <= glm_cost, "DeepSeek should be cost-effective"
    
    def test_cheapest_model_selection(self):
        """Test that cheapest model is correctly identified"""
        cheapest = ModelFactory.get_cheapest_model()
        
        # Should be DeepSeek based on our configuration
        assert cheapest == "deepseek-chat", "DeepSeek should be the cheapest model"
        
        cheapest_cost = ModelFactory.get_model_cost(cheapest)
        
        # Verify it's actually cheapest by comparing with others
        other_models = ["gpt-4o-mini", "glm-4.5", "gemini-2.0-flash"]
        for model in other_models:
            model_cost = ModelFactory.get_model_cost(model)
            assert cheapest_cost <= model_cost, f"{cheapest} should be cheaper than {model}"
    
    def test_optimal_model_selection_for_tasks(self):
        """Test optimal model selection for different task types"""
        # Test research tasks
        research_model = ModelFactory.get_optimal_model(
            task_type=TaskType.RESEARCH,
            priority="budget"
        )
        assert research_model in ["deepseek-chat", "gpt-4o-mini"], "Should select cost-effective model for research"
        
        # Test creative tasks
        creative_model = ModelFactory.get_optimal_model(
            task_type=TaskType.CREATIVE,
            priority="balanced"
        )
        assert creative_model in ["gpt-4o-mini", "glm-4.5-air", "gpt-4o"], "Should select appropriate model for creative tasks"
        
        # Test coding tasks
        coding_model = ModelFactory.get_optimal_model(
            task_type=TaskType.CODING,
            priority="budget"
        )
        assert coding_model == "deepseek-coder", "Should select DeepSeek coder for coding tasks"
    
    def test_cost_constraint_enforcement(self):
        """Test that cost constraints are enforced"""
        # Set a very low cost constraint
        low_budget_model = ModelFactory.get_optimal_model(
            task_type=TaskType.RESEARCH,
            priority="balanced",
            max_cost_per_1k=0.0002  # Very low budget
        )
        
        # Should fallback to cheapest available model
        model_cost = ModelFactory.get_model_cost(low_budget_model)
        assert model_cost <= 0.0002, "Should respect cost constraint"
    
    def test_model_comparison_functionality(self):
        """Test model comparison features"""
        models_to_compare = ["gpt-4o-mini", "deepseek-chat", "glm-4.5-air"]
        comparison = ModelFactory.compare_models(models_to_compare)
        
        assert len(comparison) == 3, "Should compare all requested models"
        
        for model_id in models_to_compare:
            assert model_id in comparison, f"Should include {model_id} in comparison"
            
            model_data = comparison[model_id]
            assert "cost_per_1k_tokens" in model_data, "Should include cost information"
            assert "cost_rank" in model_data, "Should include cost ranking"
            assert "provider" in model_data, "Should include provider information"
            assert "suitable_for" in model_data, "Should include use case information"
        
        # Verify cost rankings are correct
        cost_ranks = [comparison[model]["cost_rank"] for model in models_to_compare]
        assert sorted(cost_ranks) == [1, 2, 3], "Cost ranks should be 1, 2, 3"


class TestModelProviders:
    """Test individual model provider functionality"""
    
    def test_openai_model_configuration(self):
        """Test OpenAI model configuration"""
        # Test cost retrieval
        cost = get_openai_cost_per_token("gpt-4o-mini")
        assert cost > 0, "Should return valid cost"
        
        # Test model recommendations
        research_model = get_optimal_model(TaskType.RESEARCH, priority="budget")
        assert research_model is not None, "Should return a model recommendation"
    
    def test_deepseek_model_configuration(self):
        """Test DeepSeek model configuration"""
        # Test cost retrieval
        cost = get_deepseek_cost_per_token("deepseek-chat")
        assert cost > 0, "Should return valid cost"
        
        # DeepSeek should be very cost-effective
        assert cost < 0.0005, "DeepSeek should be very cost-effective"
    
    def test_glm_model_configuration(self):
        """Test GLM model configuration"""
        # Test cost retrieval
        cost = get_glm_cost_per_token("glm-4.5-air")
        assert cost > 0, "Should return valid cost"
        
        # GLM Flash should be the cheapest GLM option
        regular_cost = get_glm_cost_per_token("glm-4.5")
        assert cost <= regular_cost, "GLM Flash should be cheaper than regular GLM-4"


class TestCostOptimization:
    """Test cost optimization strategies"""
    
    def test_budget_priority_selection(self):
        """Test that budget priority selects cheapest options"""
        budget_model = ModelFactory.get_optimal_model(
            task_type=TaskType.SIMPLE,
            priority="budget"
        )
        
        balanced_model = ModelFactory.get_optimal_model(
            task_type=TaskType.SIMPLE,
            priority="balanced"
        )
        
        premium_model = ModelFactory.get_optimal_model(
            task_type=TaskType.SIMPLE,
            priority="premium"
        )
        
        budget_cost = ModelFactory.get_model_cost(budget_model)
        balanced_cost = ModelFactory.get_model_cost(balanced_model)
        premium_cost = ModelFactory.get_model_cost(premium_model)
        
        # Budget should be cheapest, premium should be most expensive
        assert budget_cost <= balanced_cost, "Budget model should be cheaper than balanced"
        assert balanced_cost <= premium_cost, "Balanced model should be cheaper than premium"
    
    def test_task_specific_optimization(self):
        """Test that different tasks get appropriate models"""
        coding_model = ModelFactory.get_optimal_model(TaskType.CODING, priority="budget")
        multilingual_model = ModelFactory.get_optimal_model(TaskType.MULTILINGUAL, priority="budget")
        
        # Coding should prefer DeepSeek coder
        assert coding_model == "deepseek-coder", "Coding tasks should use specialized coder model"
        
        # Multilingual should prefer GLM
        assert multilingual_model.startswith("glm"), "Multilingual tasks should prefer GLM models"
    
    def test_cost_efficiency_calculations(self):
        """Test cost efficiency calculations"""
        # Get costs for different models
        models = ["gpt-4o-mini", "deepseek-chat", "glm-4.5-air"]
        costs = [ModelFactory.get_model_cost(model) for model in models]
        
        # All costs should be reasonable
        assert all(0 < cost < 1 for cost in costs), "All costs should be between 0 and 1 dollar per 1K tokens"
        
        # Find the most cost-effective
        min_cost = min(costs)
        most_efficient = models[costs.index(min_cost)]
        
        # Should match our cheapest model
        cheapest = ModelFactory.get_cheapest_model()
        cheapest_cost = ModelFactory.get_model_cost(cheapest)
        
        assert min_cost == cheapest_cost, "Most efficient should match cheapest model"


@pytest.fixture
def mock_environment_variables():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key',
        'DEEPSEEK_API_KEY': 'test_key', 
        'GLM_API_KEY': 'test_key',
        'GOOGLE_API_KEY': 'test_key'
    }):
        yield


class TestModelCreation:
    """Test actual model creation (mocked to avoid API calls)"""
    
    @patch('app.models.openai_models.OpenAIChat')
    def test_openai_model_creation(self, mock_openai, mock_environment_variables):
        """Test OpenAI model creation"""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        model = create_openai_model("gpt-4o-mini")
        
        # Should create model with correct parameters
        mock_openai.assert_called_once()
        assert model == mock_instance
    
    @patch('app.models.deepseek_models.OpenAIChat')
    def test_deepseek_model_creation(self, mock_openai, mock_environment_variables):
        """Test DeepSeek model creation"""
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        model = create_deepseek_model("deepseek-chat")
        
        # Should create model with DeepSeek base URL
        mock_openai.assert_called_once()
        call_args = mock_openai.call_args
        assert "base_url" in call_args.kwargs
        assert "deepseek.com" in call_args.kwargs["base_url"]
    
    @patch('app.models.glm_models.GLM45Provider')
    def test_glm_model_creation(self, mock_glm_provider, mock_environment_variables):
        """Test GLM model creation"""
        mock_instance = MagicMock()
        mock_glm_provider.return_value = mock_instance
        
        model = create_glm_model("glm-4.5")
        
        # Should create model with GLM base URL
        mock_glm_provider.assert_called_once()
        call_args = mock_glm_provider.call_args
        assert "base_url" in call_args.kwargs
        assert "api.z.ai" in call_args.kwargs["base_url"]