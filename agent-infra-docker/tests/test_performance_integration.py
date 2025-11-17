"""
Performance and Integration Tests for Enhanced AgenticOS
"""

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import requests

from . import get_api_url


class TestPerformance:
    """Test performance characteristics of the enhanced system"""

    def test_agent_response_times(self, api_client: requests.Session):
        """Test that agents respond within reasonable time limits"""
        agents_to_test = [
            ("advanced-web-research-agent", "Quick research on electric vehicles"),
            ("content-writer-agent", "Write a short introduction about AI"),
            ("seo-optimizer-agent", "Analyze SEO for: Best Programming Languages"),
        ]

        for agent_id, test_message in agents_to_test:
            start_time = time.time()

            response = api_client.post(
                get_api_url(f"/agents/{agent_id}/chat"), json={"message": test_message, "stream": False}, timeout=60
            )

            response_time = time.time() - start_time

            assert response.status_code == 200, f"Agent {agent_id} should respond successfully"
            assert response_time < 60, f"Agent {agent_id} should respond within 60 seconds, took {response_time:.2f}s"

            result = response.json()
            content = result.get("content", "")
            assert len(content) > 50, f"Agent {agent_id} should provide meaningful response"

    def test_concurrent_agent_requests(self, api_client: requests.Session):
        """Test system performance under concurrent load"""

        def make_request(agent_id, message):
            """Make a single request to an agent"""
            try:
                response = api_client.post(
                    get_api_url(f"/agents/{agent_id}/chat"), json={"message": message, "stream": False}, timeout=90
                )
                return {
                    "agent_id": agent_id,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_length": len(response.text) if response.status_code == 200 else 0,
                }
            except Exception as e:
                return {"agent_id": agent_id, "status_code": 500, "success": False, "error": str(e)}

        # Test concurrent requests to different agents
        test_requests = [
            ("advanced-web-research-agent", "Research renewable energy"),
            ("content-writer-agent", "Write about technology trends"),
            ("agno-documentation-expert", "How to create an Agno agent?"),
            ("seo-optimizer-agent", "SEO analysis for tech blog"),
        ]

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(make_request, agent_id, message) for agent_id, message in test_requests]

            results = [future.result() for future in as_completed(futures, timeout=120)]

        total_time = time.time() - start_time

        # All requests should succeed
        successful_requests = sum(1 for r in results if r["success"])
        assert successful_requests >= 3, (
            f"At least 3 of 4 concurrent requests should succeed, got {successful_requests}"
        )

        # Should complete reasonably quickly despite concurrency
        assert total_time < 180, f"Concurrent requests should complete within 3 minutes, took {total_time:.2f}s"

        # All successful responses should have content
        for result in results:
            if result["success"]:
                assert result["response_length"] > 0, (
                    f"Successful response should have content for {result['agent_id']}"
                )

    def test_workflow_performance(self, api_client: requests.Session):
        """Test workflow execution performance"""
        start_time = time.time()

        response = api_client.post(
            get_api_url("/workflows/simple-blog-workflow/run"),
            json={"message": "Write a brief blog about artificial intelligence benefits", "stream": False},
            timeout=240,  # 4 minutes for workflow
        )

        execution_time = time.time() - start_time

        assert response.status_code == 200, "Workflow should execute successfully"

        # Workflow should complete within reasonable time
        assert execution_time < 240, f"Simple workflow should complete within 4 minutes, took {execution_time:.2f}s"

        result = response.json()
        content = result.get("content", "")

        # Should produce substantial content
        assert len(content) > 500, "Workflow should produce substantial blog content"

        # Should address the topic
        assert "artificial intelligence" in content.lower() or "ai" in content.lower(), (
            "Workflow should address the requested topic"
        )


class TestSystemReliability:
    """Test system reliability and error handling"""

    def test_invalid_agent_handling(self, api_client: requests.Session):
        """Test handling of requests to non-existent agents"""
        response = api_client.post(
            get_api_url("/agents/non-existent-agent/chat"), json={"message": "Test message", "stream": False}
        )

        # Should return appropriate error, not crash
        assert response.status_code in [400, 404], "Should return client error for non-existent agent"

    def test_invalid_workflow_handling(self, api_client: requests.Session):
        """Test handling of requests to non-existent workflows"""
        response = api_client.post(
            get_api_url("/workflows/non-existent-workflow/run"), json={"message": "Test message", "stream": False}
        )

        # Should return appropriate error, not crash
        assert response.status_code in [400, 404], "Should return client error for non-existent workflow"

    def test_malformed_request_handling(self, api_client: requests.Session):
        """Test handling of malformed requests"""
        # Test with invalid JSON
        response = api_client.post(
            get_api_url("/agents/advanced-web-research-agent/chat"),
            data="invalid json",  # Invalid JSON
            headers={"Content-Type": "application/json"},
        )

        # Should return 400 error, not crash
        assert response.status_code == 400, "Should return 400 for invalid JSON"

    def test_empty_message_handling(self, api_client: requests.Session):
        """Test handling of empty or very short messages"""
        test_cases = [
            {"message": ""},  # Empty message
            {"message": "hi"},  # Very short message
            {"message": "?"},  # Single character
        ]

        for test_case in test_cases:
            response = api_client.post(
                get_api_url("/agents/content-writer-agent/chat"), json=dict(test_case, stream=False), timeout=30
            )

            # Should handle gracefully, either with 200 and some content or appropriate error
            assert response.status_code in [200, 400], f"Should handle {test_case} gracefully"

            if response.status_code == 200:
                result = response.json()
                content = result.get("content", "")
                # If successful, should provide some response
                assert len(content.strip()) > 0, f"Should provide some response for {test_case}"


class TestCostOptimization:
    """Test cost optimization features"""

    def test_model_selection_efficiency(self, api_client: requests.Session):
        """Test that cost-optimized models are being used effectively"""
        # Make requests to different agents and ensure they respond
        # This indirectly tests that the cost-optimized models are working

        agents_with_expected_speed = [
            ("advanced-web-research-agent", 45),  # Should be fast with DeepSeek
            ("content-writer-agent", 60),  # GPT-4o-mini should be reasonably fast
            ("agno-documentation-expert", 60),  # GPT-4o-mini for documentation
        ]

        for agent_id, max_time in agents_with_expected_speed:
            start_time = time.time()

            response = api_client.post(
                get_api_url(f"/agents/{agent_id}/chat"),
                json={"message": "Quick test of cost-optimized performance", "stream": False},
                timeout=max_time + 15,  # Add buffer for timeout
            )

            response_time = time.time() - start_time

            assert response.status_code == 200, (
                f"Agent {agent_id} should respond successfully with cost-optimized model"
            )
            assert response_time < max_time, (
                f"Agent {agent_id} should respond quickly with cost-optimized model, took {response_time:.2f}s"
            )

            result = response.json()
            content = result.get("content", "")
            assert len(content) > 20, f"Cost-optimized {agent_id} should still provide quality responses"

    def test_team_cost_efficiency(self, api_client: requests.Session):
        """Test that research team operates efficiently"""
        start_time = time.time()

        response = api_client.post(
            get_api_url("/teams/comprehensive-research-team/chat"),
            json={"message": "Quick research on renewable energy benefits", "stream": False},
            timeout=180,  # 3 minutes should be sufficient for team research
        )

        execution_time = time.time() - start_time

        assert response.status_code == 200, "Research team should work with cost-optimized models"
        assert execution_time < 180, f"Research team should complete efficiently, took {execution_time:.2f}s"

        result = response.json()
        content = result.get("content", "")
        assert len(content) > 300, "Research team should provide comprehensive results despite cost optimization"


class TestQualityAssurance:
    """Test overall quality of the enhanced system"""

    def test_response_quality_standards(self, api_client: requests.Session):
        """Test that all agents meet quality standards"""
        quality_tests = [
            {
                "agent_id": "advanced-web-research-agent",
                "message": "Analyze the impact of climate change on agriculture",
                "expected_elements": ["climate", "agriculture", "impact", "analysis"],
                "min_length": 200,
            },
            {
                "agent_id": "content-writer-agent",
                "message": "Write an engaging introduction about space exploration",
                "expected_elements": ["space", "exploration", "introduction"],
                "min_length": 150,
            },
            {
                "agent_id": "fact-checker-agent",
                "message": "Verify: The Earth's population exceeded 8 billion in 2022",
                "expected_elements": ["verify", "population", "billion", "2022"],
                "min_length": 100,
            },
        ]

        for test in quality_tests:
            response = api_client.post(
                get_api_url(f"/agents/{test['agent_id']}/chat"),
                json={"message": test["message"], "stream": False},
                timeout=90,
            )

            assert response.status_code == 200, f"Agent {test['agent_id']} should respond successfully"

            result = response.json()
            content = result.get("content", "")
            content_lower = content.lower()

            # Check minimum length
            assert len(content) >= test["min_length"], (
                f"Agent {test['agent_id']} should provide substantial response (got {len(content)} chars, expected {test['min_length']})"
            )

            # Check for expected elements
            found_elements = sum(1 for element in test["expected_elements"] if element in content_lower)
            expected_count = len(test["expected_elements"])

            assert found_elements >= expected_count * 0.75, (
                f"Agent {test['agent_id']} should address most expected elements ({found_elements}/{expected_count})"
            )

    def test_system_consistency(self, api_client: requests.Session):
        """Test that the system provides consistent quality across multiple requests"""
        agent_id = "content-writer-agent"
        test_message = "Write about the benefits of renewable energy"

        responses = []
        for i in range(3):  # Test 3 times
            response = api_client.post(
                get_api_url(f"/agents/{agent_id}/chat"),
                json={"message": f"{test_message} (request {i + 1})", "stream": False},
                timeout=60,
            )

            assert response.status_code == 200, f"Request {i + 1} should succeed"

            result = response.json()
            content = result.get("content", "")
            responses.append(content)

        # All responses should be substantial
        for i, content in enumerate(responses):
            assert len(content) > 100, f"Response {i + 1} should be substantial"
            assert "renewable energy" in content.lower() or "renewable" in content.lower(), (
                f"Response {i + 1} should address renewable energy"
            )

        # Responses should be varied (not identical)
        assert not all(r == responses[0] for r in responses[1:]), "Responses should show variation, not be identical"


class TestDocumentationAndExamples:
    """Test that the system can be used as documented"""

    def test_basic_agent_usage_example(self, api_client: requests.Session):
        """Test basic agent usage patterns"""
        # Test the pattern shown in documentation
        response = api_client.post(
            get_api_url("/agents/agno-documentation-expert/chat"),
            json={
                "message": "Show me a simple example of creating an Agno agent with DuckDuckGo tools",
                "stream": False,
            },
            timeout=60,
        )

        assert response.status_code == 200
        result = response.json()
        content = result.get("content", "")

        # Should provide code examples
        assert "```" in content, "Should provide code examples"
        assert "agno" in content.lower(), "Should mention Agno"
        assert "agent" in content.lower(), "Should mention agents"

    def test_workflow_usage_example(self, api_client: requests.Session):
        """Test workflow usage patterns"""
        response = api_client.post(
            get_api_url("/workflows/simple-blog-workflow/run"),
            json={"message": "Create a sample blog about machine learning basics", "stream": False},
            timeout=180,
        )

        assert response.status_code == 200
        result = response.json()
        content = result.get("content", "")

        # Should create a blog post
        assert len(content) > 500, "Should create substantial blog content"
        assert "machine learning" in content.lower(), "Should address the requested topic"

    def test_research_team_usage_example(self, api_client: requests.Session):
        """Test research team usage patterns"""
        response = api_client.post(
            get_api_url("/teams/comprehensive-research-team/chat"),
            json={"message": "Research the latest developments in quantum computing", "stream": False},
            timeout=150,
        )

        assert response.status_code == 200
        result = response.json()
        content = result.get("content", "")

        # Should provide comprehensive research
        assert len(content) > 400, "Should provide comprehensive research"
        assert "quantum computing" in content.lower() or "quantum" in content.lower(), (
            "Should address quantum computing"
        )
