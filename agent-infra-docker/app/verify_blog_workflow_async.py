
import asyncio
import sys
import os
import threading
from unittest.mock import MagicMock, AsyncMock

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from agno.workflow import Workflow
    from agno.workflow.types import StepInput, StepOutput
    # Import the workflow getter
    from workflows.blog_workflow import get_blog_writing_workflow
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def main():
    print(f"Main running on thread: {threading.current_thread().name}")
    
    # Mock the agents/teams to avoid actual API calls and just verify async execution
    # We need to patch the agents used in the workflow
    # Since get_blog_writing_workflow instantiates them, we might need to mock them at module level 
    # or just let them fail on API call but verify the step execution started
    
    # For this verification, we will try to run the workflow and catch the expected error from missing API keys/models
    # or if we can mock them, that's better.
    
    # Let's try to mock the modules
    sys.modules['teams.research_team'] = MagicMock()
    sys.modules['agents.content_writer'] = MagicMock()
    sys.modules['agents.seo_optimizer'] = MagicMock()
    sys.modules['agents.fact_checker'] = MagicMock()
    
    # Setup mocks to return async mocks for arun
    mock_team = MagicMock()
    mock_team.arun = AsyncMock(return_value=MagicMock(content="Mock Research"))
    sys.modules['teams.research_team'].get_research_team.return_value = mock_team
    
    mock_writer = MagicMock()
    mock_writer.arun = AsyncMock(return_value=MagicMock(content="Mock Content"))
    sys.modules['agents.content_writer'].get_content_writer_agent.return_value = mock_writer
    
    mock_seo = MagicMock()
    sys.modules['agents.seo_optimizer'].get_seo_optimizer_agent.return_value = mock_seo
    
    mock_checker = MagicMock()
    sys.modules['agents.fact_checker'].get_fact_checker_agent.return_value = mock_checker

    # Re-import to use mocks
    if 'workflows.blog_workflow' in sys.modules:
        del sys.modules['workflows.blog_workflow']
    from workflows.blog_workflow import get_blog_writing_workflow

    print("Initializing workflow...")
    workflow = get_blog_writing_workflow(debug_mode=True)
    
    print("Running workflow with arun...")
    try:
        # Run with a simple input
        result = await workflow.arun(input="AI in Healthcare")
        print("Workflow execution completed successfully (with mocks).")
        print(f"Result Content: {result.content}")
    except Exception as e:
        print(f"Error running workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
