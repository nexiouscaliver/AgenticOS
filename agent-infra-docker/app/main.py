"""
AgenticOS - Enhanced Multi-Agent System with Advanced Capabilities

Features:
- Multi-model support (OpenAI, DeepSeek, GLM, Gemini) with cost optimization
- Specialized agents for research, content creation, and optimization
- Research team with coordinated multi-agent collaboration
- Blog writing workflow with parallel processing and quality gates
- Advanced prompts and professional-quality outputs
"""

# Load environment variables from .env file FIRST
from dotenv import load_dotenv
from pathlib import Path

# Load .env file from the parent directory (agent-infra-docker/.env)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

import asyncio
import os

from agno.os import AgentOS

# Import enhanced agents with detailed prompts
from app.agents.web_agent import get_web_agent
from app.agents.agno_assist import get_agno_assist
from app.agents.research_analyst import get_research_analyst_agent
from app.agents.content_writer import get_content_writer_agent
from app.agents.fact_checker import get_fact_checker_agent
from app.agents.seo_optimizer import get_seo_optimizer_agent
from app.agents.rag_agent import get_rag_agent
from app.agents.vision_agent import get_vision_agent
from app.processors.manager import ProcessorManager
from fastapi import UploadFile, File, HTTPException

# Import team and workflow systems
from app.teams.research_team import get_research_team
from app.workflows.blog_workflow import get_blog_writing_workflow, get_simple_blog_workflow

# Import model factory for cost optimization
from app.models.factory import ModelFactory, TaskType


def get_optimized_agents(debug_mode: bool = False):
    """
    Create optimized agent instances with cost-effective model selection
    """
    
    # Enhanced Web Search Agent with cost-optimized model
    web_agent = get_web_agent(
        model_id="deepseek-chat",  # Most cost-effective for research
        debug_mode=debug_mode
    )
    
    # Enhanced Agno Documentation Expert
    agno_assist = get_agno_assist(
        model_id="gpt-4o-mini",  # Good balance for documentation
        debug_mode=debug_mode
    )
    
    # Specialized Research Analyst
    research_analyst = get_research_analyst_agent(
        model_id="deepseek-chat",  # Cost-effective for analysis
        debug_mode=debug_mode
    )
    
    # Professional Content Writer
    content_writer = get_content_writer_agent(
        model_id="gpt-4o-mini",  # Good for creative writing
        debug_mode=debug_mode
    )
    
    # Accuracy-focused Fact Checker
    fact_checker = get_fact_checker_agent(
        model_id="gpt-4o-mini",  # Reliable for verification
        debug_mode=debug_mode
    )
    
    # SEO Optimization Specialist
    seo_optimizer = get_seo_optimizer_agent(
        model_id="gpt-4o-mini",  # Good for analytical tasks
        debug_mode=debug_mode
    )
    
    return [
        web_agent,
        agno_assist,
        research_analyst,
        content_writer,
        fact_checker,
        fact_checker,
        seo_optimizer,
        get_rag_agent(debug_mode=debug_mode),
        get_vision_agent(debug_mode=debug_mode),
    ]


def get_team_systems(debug_mode: bool = False):
    """
    Create advanced team coordination systems
    """
    
    # Comprehensive Research Team
    research_team = get_research_team(debug_mode=debug_mode)
    
    return [research_team]


def get_workflow_systems(debug_mode: bool = False):
    """
    Create automated workflow systems
    """
    
    # Comprehensive Blog Writing Workflow
    blog_workflow = get_blog_writing_workflow(debug_mode=debug_mode)
    
    # Simple Blog Workflow for basic needs
    simple_blog_workflow = get_simple_blog_workflow(debug_mode=debug_mode)
    
    return [blog_workflow, simple_blog_workflow]


# Configuration
os_config_path = str(Path(__file__).parent.joinpath("config.yaml"))

# Environment-based debug mode
debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Initialize optimized agents with cost-effective models
agents = get_optimized_agents(debug_mode=debug_mode)

# Initialize team systems
teams = get_team_systems(debug_mode=debug_mode)

# Initialize workflow systems  
workflows = get_workflow_systems(debug_mode=debug_mode)

# Create the Enhanced AgentOS with all capabilities
agent_os = AgentOS(
    os_id="agenticos-enhanced",
    agents=agents,
    teams=teams,
    workflows=workflows,
    # Configuration for the AgentOS
    config=os_config_path,
    # debug_mode=debug_mode,
)

# Get FastAPI application
app = agent_os.get_app()

processor_manager = ProcessorManager()

@app.post("/api/v1/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document."""
    temp_path = None
    processed_file_path = None
    try:
        # Save file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Process file
        chunks = await processor_manager.process_file(temp_path, file.content_type or "application/octet-stream")
        
        # Add to RAG agent's knowledge base
        rag_agent = next((a for a in agents if a.name == "RAG Assistant"), None)
        if rag_agent and rag_agent.knowledge:
            # Combine all chunks into a single document with metadata
            full_content = "\n\n".join([
                f"[Page/Section {chunk.metadata.get('page', chunk.metadata.get('rows', 'N/A'))}]\n{chunk.content}"
                for chunk in chunks
            ])
            
            # Save processed content to a temporary text file
            processed_file_path = f"/tmp/processed_{file.filename}.txt"
            with open(processed_file_path, "w", encoding="utf-8") as f:
                f.write(full_content)
            
            # Use the Knowledge API to add the file
            await rag_agent.knowledge.add_content_async(
                name=file.filename,
                path=processed_file_path,
            )
            
        return {"status": "success", "chunks": len(chunks), "filename": file.filename}
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR in upload_document: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        if processed_file_path and os.path.exists(processed_file_path):
            os.remove(processed_file_path)


async def initialize_knowledge_bases():
    """
    Initialize knowledge bases for enhanced agents
    """
    try:
        # Add comprehensive Agno documentation
        if hasattr(agents[1], 'knowledge') and agents[1].knowledge:
            await agents[1].knowledge.add_content_async(
                name="Agno Framework Documentation",
                url="https://docs.agno.com/llms-full.txt",
            )
            print("✅ Agno documentation loaded successfully")
        
        # Add additional knowledge sources
        # Note: Add more knowledge sources as needed for specialized agents
        
    except Exception as e:
        print(f"⚠️ Knowledge base initialization warning: {e}")
        print("📝 Agents will still function with web search capabilities")


if __name__ == "__main__":
    print("🚀 Starting AgenticOS Enhanced Multi-Agent System")
    print("=" * 60)
    print("📊 Available Agents:")
    for i, agent in enumerate(agents, 1):
        print(f"   {i}. {agent.name} - {agent.id}")
    
    print("🤝 Available Teams:")
    for i, team in enumerate(teams, 1):
        print(f"   {i}. {team.name} - {team.id}")
    
    print("🔄 Available Workflows:")
    for i, workflow in enumerate(workflows, 1):
        print(f"   {i}. {workflow.name} - {workflow.id}")
    
    print("💰 Cost Optimization Features:")
    print("   • Multi-model support: OpenAI, DeepSeek, GLM, Gemini")
    print("   • Intelligent model selection based on task requirements")
    print("   • Cost-effective defaults with performance optimization")
    
    print("🎯 Key Capabilities:")
    print("   • Advanced research with multi-agent coordination")
    print("   • Professional blog writing with SEO optimization")
    print("   • Fact-checking and quality assurance workflows")
    print("   • Comprehensive documentation assistance")
    
    print("⚙️ Initialization:")
    print("   • Loading knowledge bases...")
    
    # Initialize knowledge bases asynchronously
    asyncio.run(initialize_knowledge_bases())
    
    print("   • Starting web server...")
    print("=" * 60)
    
    # Start the enhanced AgentOS
    agent_os.serve(app="main:app", reload=True)