"""
AgenticOS - Enhanced Multi-Agent System with Advanced Capabilities

Features:
- Local GLM model support with cost optimization
- Specialized agents for research, content creation, and optimization
- Research team with coordinated multi-agent collaboration
- Blog writing workflow with parallel processing and quality gates
- Advanced prompts and professional-quality outputs
"""

import argparse
import asyncio
import os
from pathlib import Path

from agno.os import AgentOS
from agno.db.postgres import PostgresDb

# Import enhanced agents with detailed prompts
from agents.web_agent import get_web_agent
from agents.agno_assist import get_agno_assist
from agents.research_analyst import get_research_analyst_agent
from agents.content_writer import get_content_writer_agent
from agents.fact_checker import get_fact_checker_agent
from agents.seo_optimizer import get_seo_optimizer_agent
from agents.rag_agent import get_rag_agent

# Import team and workflow systems
from teams.research_team import get_research_team
from workflows.blog_workflow import get_blog_writing_workflow, get_simple_blog_workflow

# Import model factory for cost optimization
from models.factory import ModelFactory, TaskType
from db.session import db_url
from registry import get_registry
import dotenv
dotenv.load_dotenv()

def get_optimized_agents(debug_mode: bool = False):
    """
    Create optimized agent instances with cost-effective model selection
    """
    
    # Enhanced Web Search Agent with cost-optimized model
    web_agent = get_web_agent(
        model_id="gemini-2.5-flash-lite",  # Most cost-effective for research
        debug_mode=debug_mode
    )
    
    # Enhanced Agno Documentation Expert
    agno_assist = get_agno_assist(
        model_id="gemini-2.5-flash-lite",  # Good balance for documentation
        debug_mode=debug_mode
    )
    
    # Specialized Research Analyst
    research_analyst = get_research_analyst_agent(
        model_id="gemini-2.5-flash-lite",  # Cost-effective for analysis
        debug_mode=debug_mode
    )
    
    # Professional Content Writer
    content_writer = get_content_writer_agent(
        model_id="gemini-2.5-flash-lite",  # Good for creative writing
        debug_mode=debug_mode
    )
    
    # Accuracy-focused Fact Checker
    fact_checker = get_fact_checker_agent(
        model_id="gemini-2.5-flash-lite",  # Reliable for verification
        debug_mode=debug_mode
    )
    
    # SEO Optimization Specialist
    seo_optimizer = get_seo_optimizer_agent(
        model_id="gemini-2.5-flash-lite",  # Good for analytical tasks
        debug_mode=debug_mode
    )
    
    # Versatile RAG Agent
    rag_agent = get_rag_agent(
        model_id="gemini-2.5-flash-lite",
        debug_mode=debug_mode
    )
    
    return [
        web_agent,
        agno_assist,
        research_analyst,
        content_writer,
        fact_checker,
        seo_optimizer,
        rag_agent,
    ]


def get_team_systems(debug_mode: bool = False):
    """
    Create advanced team coordination systems
    """
    
    # Comprehensive Research Team with GLM model for coordination
    research_team = get_research_team(model_id="gemini-2.5-flash-lite", debug_mode=debug_mode)
    
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
    agents=agents,
    teams=teams,
    workflows=workflows,
    # Shared database for session/memory storage (required in agno 2.6+)
    db=PostgresDb(db_url=db_url),
    # Registry exposes tools/models/dbs to AgentOS Studio for visual building
    registry=get_registry(),
    # Configuration for the AgentOS
    config=os_config_path,
    # debug_mode=debug_mode,
)

# Get FastAPI application
app = agent_os.get_app()


DEFAULT_KB_URL = "https://docs.agno.com/llms-full.txt"


async def initialize_knowledge_bases(kb_url: str):
    """Load a URL into the Agno Assist knowledge base."""
    try:
        if hasattr(agents[1], 'knowledge') and agents[1].knowledge:
            await agents[1].knowledge.add_content_async(
                name="Agno Framework Documentation",
                url=kb_url,
            )
            print(f"✅ Knowledge base loaded: {kb_url}")
    except Exception as e:
        print(f"⚠️ Knowledge base initialization warning: {e}")
        print("📝 Agents will still function with web search capabilities")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgenticOS Multi-Agent System")
    parser.add_argument(
        "--loadkb",
        nargs="?",
        const=DEFAULT_KB_URL,
        default=None,
        metavar="URL",
        help=f"Load a URL into the knowledge base before starting. "
             f"Omit URL to use the default: {DEFAULT_KB_URL}",
    )
    args = parser.parse_args()

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

    print("🎯 Key Capabilities:")
    print("   • Advanced research with multi-agent coordination")
    print("   • Professional blog writing with SEO optimization")
    print("   • Fact-checking and quality assurance workflows")
    print("   • Comprehensive documentation assistance")

    print("⚙️ Initialization:")
    if args.loadkb:
        print(f"   • Loading knowledge base from: {args.loadkb}")
        asyncio.run(initialize_knowledge_bases(args.loadkb))
    else:
        print("   • Skipping knowledge base load (use --loadkb to enable)")

    print("   • Starting web server...")
    print("=" * 60)

    agent_os.serve(app="main:app", reload=False)