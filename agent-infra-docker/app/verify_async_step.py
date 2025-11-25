
import asyncio
import sys
import os
import threading
import time

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from agno.workflow import Workflow, Step
    from agno.workflow.types import StepInput, StepOutput
except ImportError:
    print("Could not import agno. Make sure you are running in the correct environment.")
    sys.exit(1)

async def async_step_function(step_input: StepInput) -> StepOutput:
    thread_name = threading.current_thread().name
    print(f"Async Step running on thread: {thread_name}")
    # Simulate async work
    await asyncio.sleep(1)
    return StepOutput(content=f"Async Result from {thread_name}")

step = Step(
    name="Async Step",
    executor=async_step_function,
    description="An async step"
)

workflow = Workflow(
    id="async-test-workflow",
    name="Async Test Workflow",
    steps=[step]
)

async def main():
    print(f"Main running on thread: {threading.current_thread().name}")
    print("Running workflow with arun...")
    try:
        # We need to mock the session and other things usually handled by AgentOS or manually
        # But arun should handle basic execution
        result = await workflow.arun(input="test")
        print(f"Workflow Result: {result.content}")
    except Exception as e:
        print(f"Error running workflow: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
