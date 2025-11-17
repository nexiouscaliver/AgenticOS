#!/usr/bin/env python3
"""
Comprehensive test script for all agents, teams, and workflows in AgenticOS
Tests instantiation, configuration, and basic functionality of all components
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add agent-infra-docker/app to path
sys.path.insert(0, str(Path(__file__).parent / "agent-infra-docker" / "app"))

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.error = None
        self.details = {}

    def mark_passed(self, details: Dict[str, Any] = None):
        self.passed = True
        self.details = details or {}

    def mark_failed(self, error: str):
        self.passed = False
        self.error = error

class ComponentTester:
    def __init__(self):
        self.results: List[TestResult] = []
        self.agents_tested = 0
        self.teams_tested = 0
        self.workflows_tested = 0

    def print_header(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}\n")

    def print_section(self, text: str):
        print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
        print(f"{Colors.BLUE}{'-'*len(text)}{Colors.END}")

    def print_success(self, text: str):
        print(f"{Colors.GREEN}✓{Colors.END} {text}")

    def print_failure(self, text: str):
        print(f"{Colors.RED}✗{Colors.END} {text}")

    def print_info(self, text: str):
        print(f"{Colors.YELLOW}ℹ{Colors.END} {text}")

    def test_agent(self, name: str, agent_factory, model_id: str = "gpt-4o-mini") -> TestResult:
        """Test individual agent instantiation and configuration"""
        result = TestResult(f"Agent: {name}")

        try:
            # Try to instantiate the agent
            agent = agent_factory(model_id=model_id, debug_mode=False)

            # Validate agent properties
            if not hasattr(agent, 'id'):
                result.mark_failed("Agent missing 'id' attribute")
                return result

            if not hasattr(agent, 'name'):
                result.mark_failed("Agent missing 'name' attribute")
                return result

            if not hasattr(agent, 'model'):
                result.mark_failed("Agent missing 'model' attribute")
                return result

            # Collect agent details
            details = {
                'id': agent.id,
                'name': agent.name,
                'has_tools': hasattr(agent, 'tools') and agent.tools is not None,
                'tool_count': len(agent.tools) if hasattr(agent, 'tools') and agent.tools else 0,
                'has_description': hasattr(agent, 'description') and bool(agent.description),
                'has_instructions': hasattr(agent, 'instructions') and bool(agent.instructions),
                'has_db': hasattr(agent, 'db') and agent.db is not None,
                'has_knowledge': hasattr(agent, 'knowledge') and agent.knowledge is not None,
            }

            result.mark_passed(details)
            self.agents_tested += 1

        except Exception as e:
            result.mark_failed(f"Failed to instantiate: {str(e)}")

        self.results.append(result)
        return result

    def test_team(self, name: str, team_factory) -> TestResult:
        """Test team instantiation and configuration"""
        result = TestResult(f"Team: {name}")

        try:
            # Try to instantiate the team
            team = team_factory(debug_mode=False)

            # Validate team properties
            if not hasattr(team, 'id'):
                result.mark_failed("Team missing 'id' attribute")
                return result

            if not hasattr(team, 'name'):
                result.mark_failed("Team missing 'name' attribute")
                return result

            # Collect team details
            details = {
                'id': team.id,
                'name': team.name,
                'has_agents': hasattr(team, 'agents') and team.agents is not None,
                'agent_count': len(team.agents) if hasattr(team, 'agents') and team.agents else 0,
                'has_description': hasattr(team, 'description') and bool(team.description),
            }

            result.mark_passed(details)
            self.teams_tested += 1

        except Exception as e:
            result.mark_failed(f"Failed to instantiate: {str(e)}")

        self.results.append(result)
        return result

    def test_workflow(self, name: str, workflow_factory) -> TestResult:
        """Test workflow instantiation and configuration"""
        result = TestResult(f"Workflow: {name}")

        try:
            # Try to instantiate the workflow
            workflow = workflow_factory(debug_mode=False)

            # Validate workflow properties
            if not hasattr(workflow, 'id'):
                result.mark_failed("Workflow missing 'id' attribute")
                return result

            if not hasattr(workflow, 'name'):
                result.mark_failed("Workflow missing 'name' attribute")
                return result

            # Collect workflow details
            details = {
                'id': workflow.id,
                'name': workflow.name,
                'has_agents': hasattr(workflow, 'agents') and workflow.agents is not None,
                'agent_count': len(workflow.agents) if hasattr(workflow, 'agents') and workflow.agents else 0,
                'has_description': hasattr(workflow, 'description') and bool(workflow.description),
            }

            result.mark_passed(details)
            self.workflows_tested += 1

        except Exception as e:
            result.mark_failed(f"Failed to instantiate: {str(e)}")

        self.results.append(result)
        return result

    def print_results_summary(self):
        """Print comprehensive test results summary"""
        self.print_header("TEST RESULTS SUMMARY")

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\n{Colors.BOLD}Overall Results:{Colors.END}")
        print(f"  Total Tests:  {total}")
        print(f"  {Colors.GREEN}Passed:{Colors.END}       {passed}")
        print(f"  {Colors.RED}Failed:{Colors.END}       {failed}")
        print(f"  Success Rate: {(passed/total*100) if total > 0 else 0:.1f}%")

        print(f"\n{Colors.BOLD}Components Tested:{Colors.END}")
        print(f"  Agents:    {self.agents_tested}")
        print(f"  Teams:     {self.teams_tested}")
        print(f"  Workflows: {self.workflows_tested}")

        # Detailed results
        self.print_section("Detailed Results")

        for result in self.results:
            if result.passed:
                self.print_success(result.name)
                if result.details:
                    for key, value in result.details.items():
                        print(f"    {key}: {value}")
            else:
                self.print_failure(f"{result.name}")
                if result.error:
                    print(f"    Error: {result.error}")

        # Final status
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}ALL TESTS PASSED! ✓{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}SOME TESTS FAILED ✗{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

        return failed == 0

def main():
    """Run all component tests"""
    tester = ComponentTester()

    tester.print_header("AgenticOS Component Testing Suite")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Import all agent factories
    tester.print_section("Testing Agents (6 total)")

    try:
        from agents.web_agent import get_web_agent
        result = tester.test_agent("Web Agent", get_web_agent, "deepseek-chat")
        if result.passed:
            tester.print_success(f"Web Agent ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Web Agent - {result.error}")
    except Exception as e:
        tester.print_failure(f"Web Agent - Import failed: {str(e)}")
        tester.results.append(TestResult("Agent: Web Agent"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    try:
        from agents.agno_assist import get_agno_assist
        result = tester.test_agent("Agno Assist", get_agno_assist, "gpt-4o-mini")
        if result.passed:
            tester.print_success(f"Agno Assist ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Agno Assist - {result.error}")
    except Exception as e:
        tester.print_failure(f"Agno Assist - Import failed: {str(e)}")
        tester.results.append(TestResult("Agent: Agno Assist"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    try:
        from agents.research_analyst import get_research_analyst_agent
        result = tester.test_agent("Research Analyst", get_research_analyst_agent, "deepseek-chat")
        if result.passed:
            tester.print_success(f"Research Analyst ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Research Analyst - {result.error}")
    except Exception as e:
        tester.print_failure(f"Research Analyst - Import failed: {str(e)}")
        tester.results.append(TestResult("Agent: Research Analyst"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    try:
        from agents.content_writer import get_content_writer_agent
        result = tester.test_agent("Content Writer", get_content_writer_agent, "gpt-4o-mini")
        if result.passed:
            tester.print_success(f"Content Writer ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Content Writer - {result.error}")
    except Exception as e:
        tester.print_failure(f"Content Writer - Import failed: {str(e)}")
        tester.results.append(TestResult("Agent: Content Writer"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    try:
        from agents.fact_checker import get_fact_checker_agent
        result = tester.test_agent("Fact Checker", get_fact_checker_agent, "gpt-4o-mini")
        if result.passed:
            tester.print_success(f"Fact Checker ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Fact Checker - {result.error}")
    except Exception as e:
        tester.print_failure(f"Fact Checker - Import failed: {str(e)}")
        tester.results.append(TestResult("Agent: Fact Checker"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    try:
        from agents.seo_optimizer import get_seo_optimizer_agent
        result = tester.test_agent("SEO Optimizer", get_seo_optimizer_agent, "gpt-4o-mini")
        if result.passed:
            tester.print_success(f"SEO Optimizer ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"SEO Optimizer - {result.error}")
    except Exception as e:
        tester.print_failure(f"SEO Optimizer - Import failed: {str(e)}")
        tester.results.append(TestResult("Agent: SEO Optimizer"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    # Test teams
    tester.print_section("Testing Teams (1 total)")

    try:
        from teams.research_team import get_research_team
        result = tester.test_team("Research Team", get_research_team)
        if result.passed:
            tester.print_success(f"Research Team ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Research Team - {result.error}")
    except Exception as e:
        tester.print_failure(f"Research Team - Import failed: {str(e)}")
        tester.results.append(TestResult("Team: Research Team"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    # Test workflows
    tester.print_section("Testing Workflows (2 total)")

    try:
        from workflows.blog_workflow import get_blog_writing_workflow
        result = tester.test_workflow("Blog Writing Workflow", get_blog_writing_workflow)
        if result.passed:
            tester.print_success(f"Blog Writing Workflow ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Blog Writing Workflow - {result.error}")
    except Exception as e:
        tester.print_failure(f"Blog Writing Workflow - Import failed: {str(e)}")
        tester.results.append(TestResult("Workflow: Blog Writing Workflow"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    try:
        from workflows.blog_workflow import get_simple_blog_workflow
        result = tester.test_workflow("Simple Blog Workflow", get_simple_blog_workflow)
        if result.passed:
            tester.print_success(f"Simple Blog Workflow ({result.details.get('id', 'unknown')})")
        else:
            tester.print_failure(f"Simple Blog Workflow - {result.error}")
    except Exception as e:
        tester.print_failure(f"Simple Blog Workflow - Import failed: {str(e)}")
        tester.results.append(TestResult("Workflow: Simple Blog Workflow"))
        tester.results[-1].mark_failed(f"Import failed: {str(e)}")

    # Print final summary
    success = tester.print_results_summary()

    # Return exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
