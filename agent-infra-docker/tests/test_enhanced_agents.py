"""
Enhanced Agents Integration Tests
"""

import pytest
import requests

from . import get_api_url


class TestEnhancedAgents:
    """Test enhanced agents with detailed prompts and capabilities"""

    @pytest.mark.parametrize(
        "agent_name",
        [
            "advanced-web-research-agent",
            "agno-documentation-expert",
            "research-analyst-agent",
            "content-writer-agent",
            "fact-checker-agent",
            "seo-optimizer-agent",
        ],
    )
    def test_enhanced_agent_availability(self, api_client: requests.Session, agent_name: str):
        """Test that all enhanced agents are available"""
        response = api_client.get(get_api_url("/agents"))
        assert response.status_code == 200

        agents_data = response.json()
        agent_ids = [agent["id"] for agent in agents_data.get("agents", [])]

        assert agent_name in agent_ids, f"Agent {agent_name} not found in available agents"

    def test_web_research_agent_enhanced_capability(self, api_client: requests.Session):
        """Test advanced web research agent capabilities"""
        response = api_client.post(
            get_api_url("/agents/advanced-web-research-agent/chat"),
            json={"message": "Research the latest developments in AI model efficiency", "stream": False},
        )

        assert response.status_code == 200
        result = response.json()

        # Check for enhanced research characteristics
        content = result.get("content", "").lower()

        # Should have research methodology indicators
        research_indicators = ["research", "sources", "analysis", "findings"]
        assert any(indicator in content for indicator in research_indicators)

        # Should be comprehensive (longer response)
        assert len(content) > 500, "Enhanced research should be comprehensive"

    def test_agno_documentation_expert(self, api_client: requests.Session):
        """Test Agno documentation expert capabilities"""
        response = api_client.post(
            get_api_url("/agents/agno-documentation-expert/chat"),
            json={"message": "How do I create a basic Agno agent with tools?", "stream": False},
        )

        assert response.status_code == 200
        result = response.json()

        content = result.get("content", "").lower()

        # Should have Agno-specific information
        agno_indicators = ["agno", "agent", "tools", "import", "code"]
        assert any(indicator in content for indicator in agno_indicators)

        # Should provide code examples
        assert "```" in result.get("content", ""), "Should include code examples"

    def test_research_analyst_methodology(self, api_client: requests.Session):
        """Test research analyst methodology and structure"""
        response = api_client.post(
            get_api_url("/agents/research-analyst-agent/chat"),
            json={"message": "Analyze the market trends in renewable energy adoption", "stream": False},
        )

        assert response.status_code == 200
        result = response.json()

        content = result.get("content", "").lower()

        # Should show academic methodology
        methodology_indicators = ["analysis", "data", "trends", "methodology", "findings"]
        assert any(indicator in content for indicator in methodology_indicators)

        # Should be structured and professional
        assert len(content) > 300, "Analysis should be comprehensive"

    def test_content_writer_quality(self, api_client: requests.Session):
        """Test content writer professional quality"""
        response = api_client.post(
            get_api_url("/agents/content-writer-agent/chat"),
            json={"message": "Write an introduction for a blog about sustainable technology", "stream": False},
        )

        assert response.status_code == 200
        result = response.json()

        content = result.get("content", "")

        # Should be engaging and well-structured
        assert len(content) > 200, "Content should be substantial"

        # Should have professional writing characteristics
        professional_indicators = ["introduction", "sustainable", "technology"]
        assert any(indicator in content.lower() for indicator in professional_indicators)

    def test_fact_checker_verification_process(self, api_client: requests.Session):
        """Test fact checker verification capabilities"""
        response = api_client.post(
            get_api_url("/agents/fact-checker-agent/chat"),
            json={"message": "Verify this claim: Solar energy costs have decreased by 90% since 2010", "stream": False},
        )

        assert response.status_code == 200
        result = response.json()

        content = result.get("content", "").lower()

        # Should show verification methodology
        verification_indicators = ["verify", "claim", "sources", "evidence", "accuracy"]
        assert any(indicator in content for indicator in verification_indicators)

    def test_seo_optimizer_recommendations(self, api_client: requests.Session):
        """Test SEO optimizer analysis capabilities"""
        response = api_client.post(
            get_api_url("/agents/seo-optimizer-agent/chat"),
            json={"message": "Optimize this content for SEO: 'Best Practices for Remote Work'", "stream": False},
        )

        assert response.status_code == 200
        result = response.json()

        content = result.get("content", "").lower()

        # Should provide SEO recommendations
        seo_indicators = ["seo", "keywords", "optimization", "search", "ranking"]
        assert any(indicator in content for indicator in seo_indicators)

    def test_cost_optimized_models(self, api_client: requests.Session):
        """Test that agents are using cost-optimized models"""
        # This is more of an integration test to ensure the system starts successfully
        # with the cost-optimized model configuration

        response = api_client.get(get_api_url("/agents"))
        assert response.status_code == 200

        agents_data = response.json()
        assert len(agents_data.get("agents", [])) >= 6, "Should have at least 6 enhanced agents"

    def test_agent_response_quality_standards(self, api_client: requests.Session):
        """Test that all agents meet basic quality standards"""
        test_agents = [
            ("advanced-web-research-agent", "What are the benefits of electric vehicles?"),
            ("content-writer-agent", "Write a brief about artificial intelligence"),
            ("research-analyst-agent", "Analyze cryptocurrency market trends"),
        ]

        for agent_id, test_message in test_agents:
            response = api_client.post(
                get_api_url(f"/agents/{agent_id}/chat"), json={"message": test_message, "stream": False}
            )

            assert response.status_code == 200
            result = response.json()

            # Quality standards
            content = result.get("content", "")
            assert len(content) > 100, f"Agent {agent_id} should provide substantial responses"
            assert content.strip(), f"Agent {agent_id} should not return empty responses"

            # Should not contain error messages in normal operation
            error_indicators = ["error", "failed", "exception", "traceback"]
            content_lower = content.lower()
            assert not any(indicator in content_lower for indicator in error_indicators), (
                f"Agent {agent_id} should not return error messages for normal queries"
            )
