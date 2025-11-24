#!/usr/bin/env python3
"""
Component Definition Tester - Tests the structure and configuration of agents, teams, and workflows
This script validates Python files without requiring runtime dependencies
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class ComponentDefinition:
    """Represents a component definition extracted from source code"""
    def __init__(self, name: str, file_path: Path):
        self.name = name
        self.file_path = file_path
        self.factory_function = None
        self.agent_id = None
        self.agent_name = None
        self.has_model = False
        self.has_tools = False
        self.has_description = False
        self.has_instructions = False
        self.has_db = False
        self.has_knowledge = False
        self.imports = []
        self.errors = []

class ComponentTester:
    def __init__(self):
        self.agents = []
        self.teams = []
        self.workflows = []
        self.base_path = Path(__file__).parent / "agent-infra-docker" / "app"

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

    def print_warning(self, text: str):
        print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

    def print_info(self, text: str, indent=0):
        prefix = "  " * indent
        print(f"{prefix}{Colors.YELLOW}•{Colors.END} {text}")

    def extract_string_value(self, node) -> Optional[str]:
        """Extract string value from an AST node"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Str):  # Python < 3.8
            return node.s
        elif isinstance(node, ast.Call) and hasattr(node.func, 'id'):
            if node.func.id == 'dedent' and node.args:
                return self.extract_string_value(node.args[0])
        return None

    def analyze_agent_file(self, file_path: Path) -> Optional[ComponentDefinition]:
        """Analyze an agent Python file and extract configuration"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            tree = ast.parse(content)
            comp = ComponentDefinition(file_path.stem, file_path)

            # Find the get_* function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith('get_'):
                    comp.factory_function = node.name

                    # Analyze the function body for Agent/Team/Workflow creation
                    for stmt in ast.walk(node):
                        if isinstance(stmt, ast.Call):
                            # Check for Agent(), Team(), or Workflow() construction
                            func_name = None
                            if isinstance(stmt.func, ast.Name):
                                func_name = stmt.func.id
                            elif isinstance(stmt.func, ast.Attribute):
                                func_name = stmt.func.attr

                            if func_name in ['Agent', 'Team', 'Workflow']:
                                # Extract keyword arguments
                                for keyword in stmt.keywords:
                                    if keyword.arg == 'id':
                                        comp.agent_id = self.extract_string_value(keyword.value)
                                    elif keyword.arg == 'name':
                                        comp.agent_name = self.extract_string_value(keyword.value)
                                    elif keyword.arg == 'model':
                                        comp.has_model = True
                                    elif keyword.arg == 'tools':
                                        comp.has_tools = True
                                    elif keyword.arg == 'description':
                                        val = self.extract_string_value(keyword.value)
                                        comp.has_description = val is not None and len(val.strip()) > 0
                                    elif keyword.arg == 'instructions':
                                        val = self.extract_string_value(keyword.value)
                                        comp.has_instructions = val is not None and len(val.strip()) > 0
                                    elif keyword.arg == 'db':
                                        comp.has_db = True
                                    elif keyword.arg == 'knowledge':
                                        comp.has_knowledge = True

                # Collect imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        comp.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        comp.imports.append(node.module)

            if not comp.factory_function:
                comp.errors.append("No factory function (get_*) found")

            if not comp.agent_id:
                comp.errors.append("No agent/team/workflow ID found")

            return comp

        except Exception as e:
            comp = ComponentDefinition(file_path.stem, file_path)
            comp.errors.append(f"Parse error: {str(e)}")
            return comp

    def test_agents(self):
        """Test all agent definitions"""
        self.print_section("Testing Agent Definitions (6 expected)")

        agents_dir = self.base_path / "agents"
        agent_files = [f for f in agents_dir.glob("*.py") if f.stem != "__init__"]

        for agent_file in sorted(agent_files):
            comp = self.analyze_agent_file(agent_file)

            if comp.errors:
                self.print_failure(f"{agent_file.stem}")
                for error in comp.errors:
                    self.print_info(f"Error: {error}", indent=1)
            else:
                self.print_success(f"{agent_file.stem}")
                self.print_info(f"ID: {comp.agent_id}", indent=1)
                if comp.agent_name:
                    self.print_info(f"Name: {comp.agent_name}", indent=1)
                self.print_info(f"Factory: {comp.factory_function}()", indent=1)

                features = []
                if comp.has_model:
                    features.append("Model")
                if comp.has_tools:
                    features.append("Tools")
                if comp.has_description:
                    features.append("Description")
                if comp.has_instructions:
                    features.append("Instructions")
                if comp.has_db:
                    features.append("Database")
                if comp.has_knowledge:
                    features.append("Knowledge")

                if features:
                    self.print_info(f"Features: {', '.join(features)}", indent=1)

            self.agents.append(comp)

    def test_teams(self):
        """Test all team definitions"""
        self.print_section("Testing Team Definitions (1 expected)")

        teams_dir = self.base_path / "teams"
        team_files = [f for f in teams_dir.glob("*.py") if f.stem != "__init__"]

        for team_file in sorted(team_files):
            comp = self.analyze_agent_file(team_file)

            if comp.errors:
                self.print_failure(f"{team_file.stem}")
                for error in comp.errors:
                    self.print_info(f"Error: {error}", indent=1)
            else:
                self.print_success(f"{team_file.stem}")
                self.print_info(f"ID: {comp.agent_id}", indent=1)
                if comp.agent_name:
                    self.print_info(f"Name: {comp.agent_name}", indent=1)
                self.print_info(f"Factory: {comp.factory_function}()", indent=1)

            self.teams.append(comp)

    def test_workflows(self):
        """Test all workflow definitions"""
        self.print_section("Testing Workflow Definitions (2 expected)")

        workflows_dir = self.base_path / "workflows"

        # Read blog_workflow.py which contains multiple workflow factories
        workflow_file = workflows_dir / "blog_workflow.py"

        if workflow_file.exists():
            try:
                with open(workflow_file, 'r') as f:
                    content = f.read()
                tree = ast.parse(content)

                workflow_functions = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('get_'):
                        workflow_functions.append(node.name)

                # Analyze each workflow factory function
                for func_name in workflow_functions:
                    comp = ComponentDefinition(func_name, workflow_file)
                    comp.factory_function = func_name

                    # Try to extract workflow ID by looking for Workflow construction
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name == func_name:
                            for stmt in ast.walk(node):
                                if isinstance(stmt, ast.Call):
                                    func_id = None
                                    if isinstance(stmt.func, ast.Name):
                                        func_id = stmt.func.id
                                    elif isinstance(stmt.func, ast.Attribute):
                                        func_id = stmt.func.attr

                                    if func_id == 'Workflow':
                                        for keyword in stmt.keywords:
                                            if keyword.arg == 'id':
                                                comp.agent_id = self.extract_string_value(keyword.value)
                                            elif keyword.arg == 'name':
                                                comp.agent_name = self.extract_string_value(keyword.value)
                                            elif keyword.arg == 'description':
                                                val = self.extract_string_value(keyword.value)
                                                comp.has_description = val is not None

                    if comp.agent_id:
                        self.print_success(f"{func_name}")
                        self.print_info(f"ID: {comp.agent_id}", indent=1)
                        if comp.agent_name:
                            self.print_info(f"Name: {comp.agent_name}", indent=1)
                        self.workflows.append(comp)
                    else:
                        self.print_warning(f"{func_name} - Could not extract workflow ID")
                        comp.errors.append("Could not extract workflow ID")
                        self.workflows.append(comp)

            except Exception as e:
                self.print_failure(f"blog_workflow.py - Parse error: {str(e)}")
        else:
            self.print_failure("blog_workflow.py not found")

    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")

        agents_ok = sum(1 for a in self.agents if not a.errors)
        teams_ok = sum(1 for t in self.teams if not t.errors)
        workflows_ok = sum(1 for w in self.workflows if not w.errors)

        print(f"{Colors.BOLD}Components Found and Validated:{Colors.END}")
        print(f"  Agents:    {agents_ok}/{len(self.agents)} OK")
        print(f"  Teams:     {teams_ok}/{len(self.teams)} OK")
        print(f"  Workflows: {workflows_ok}/{len(self.workflows)} OK")

        total_ok = agents_ok + teams_ok + workflows_ok
        total = len(self.agents) + len(self.teams) + len(self.workflows)

        print(f"\n{Colors.BOLD}Overall Status:{Colors.END}")
        print(f"  Total: {total_ok}/{total} components validated")
        print(f"  Success Rate: {(total_ok/total*100) if total > 0 else 0:.1f}%")

        if total_ok == total and total > 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}ALL COMPONENTS VALIDATED SUCCESSFULLY! ✓{Colors.END}")

            # Print component list
            print(f"\n{Colors.BOLD}Available Components:{Colors.END}")
            print(f"\n{Colors.BOLD}Agents ({len(self.agents)}):{Colors.END}")
            for agent in self.agents:
                print(f"  • {agent.agent_id or agent.name} ({agent.factory_function})")

            print(f"\n{Colors.BOLD}Teams ({len(self.teams)}):{Colors.END}")
            for team in self.teams:
                print(f"  • {team.agent_id or team.name} ({team.factory_function})")

            print(f"\n{Colors.BOLD}Workflows ({len(self.workflows)}):{Colors.END}")
            for workflow in self.workflows:
                print(f"  • {workflow.agent_id or workflow.name} ({workflow.factory_function})")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}SOME COMPONENTS HAVE ISSUES ✗{Colors.END}")

            if any(a.errors for a in self.agents):
                print(f"\n{Colors.RED}Agents with errors:{Colors.END}")
                for agent in self.agents:
                    if agent.errors:
                        print(f"  • {agent.name}: {', '.join(agent.errors)}")

            if any(t.errors for t in self.teams):
                print(f"\n{Colors.RED}Teams with errors:{Colors.END}")
                for team in self.teams:
                    if team.errors:
                        print(f"  • {team.name}: {', '.join(team.errors)}")

            if any(w.errors for w in self.workflows):
                print(f"\n{Colors.RED}Workflows with errors:{Colors.END}")
                for workflow in self.workflows:
                    if workflow.errors:
                        print(f"  • {workflow.name}: {', '.join(workflow.errors)}")

        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}\n")

        return total_ok == total and total > 0

def main():
    """Main test runner"""
    tester = ComponentTester()

    tester.print_header("AgenticOS Component Definition Validator")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base path: {tester.base_path}\n")

    # Run tests
    tester.test_agents()
    tester.test_teams()
    tester.test_workflows()

    # Print summary
    success = tester.print_summary()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
