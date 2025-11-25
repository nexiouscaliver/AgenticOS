"""
Blog Writing Workflow - Comprehensive blog creation with research team and optimization
"""

from textwrap import dedent
from dotenv import load_dotenv

load_dotenv()
from agno.workflow import Workflow, Step, Parallel, Condition
from agno.workflow.types import StepInput, StepOutput
from agno.db.postgres import PostgresDb

from teams.research_team import get_research_team
from agents.content_writer import get_content_writer_agent
from agents.seo_optimizer import get_seo_optimizer_agent
from agents.fact_checker import get_fact_checker_agent
from db.session import db_url


def get_blog_writing_workflow(debug_mode: bool = False) -> Workflow:
    """
    Comprehensive Blog Writing Workflow
    
    Process Flow:
    1. Topic Analysis & Planning
    2. Parallel Research (Research Team + Competitive Analysis)
    3. Content Planning & Structure
    4. Blog Writing
    5. Parallel Enhancement (SEO + Fact-checking)
    6. Final Review & Polish
    
    Features:
    - Multi-agent research team for comprehensive information gathering
    - Parallel execution for efficiency
    - Quality gates and conditional processing
    - SEO optimization and fact-checking integration
    - Professional blog creation with citations and optimization
    """
    
    # Initialize agents
    research_team = get_research_team(debug_mode=debug_mode)
    content_writer = get_content_writer_agent(debug_mode=debug_mode)
    seo_optimizer = get_seo_optimizer_agent(debug_mode=debug_mode)
    fact_checker = get_fact_checker_agent(debug_mode=debug_mode)
    
    # Custom step functions for workflow optimization
    async def topic_analysis_function(step_input: StepInput) -> StepOutput:
        """
        Analyze blog topic and create research strategy
        """
        topic = step_input.input
        
        analysis_prompt = f"""
        BLOG TOPIC ANALYSIS & RESEARCH STRATEGY

        Topic: {topic}

        Please provide:
        1. **Topic Breakdown**: Main subject and key subtopics to cover
        2. **Target Audience**: Who would be interested in this topic
        3. **Research Areas**: 5-6 specific areas for comprehensive research
        4. **Content Goals**: What value this blog should provide readers
        5. **SEO Opportunities**: Potential keywords and search intent
        6. **Competitive Landscape**: What existing content exists on this topic

        Format as structured analysis for the research team.
        """
        
        try:
            # Use research team for initial analysis
            response = await research_team.arun(analysis_prompt)
            
            return StepOutput(
                content=f"""
                ## Topic Analysis Complete

                **Blog Topic**: {topic}

                **Research Strategy**:
                {response.content}

                **Next Step**: Comprehensive research execution by specialized team
                """.strip()
            )
        except Exception as e:
            return StepOutput(
                content=f"Topic analysis failed: {str(e)}",
                success=False,
            )
    
    async def content_planning_function(step_input: StepInput) -> StepOutput:
        """
        Create detailed content plan based on research findings
        """
        topic = step_input.input
        research_content = step_input.previous_step_content
        
        planning_prompt = f"""
        COMPREHENSIVE CONTENT PLANNING

        Original Topic: {topic}

        Research Findings:
        {research_content[:2000] if research_content else "No research available"}

        Create a detailed blog content plan including:
        1. **Blog Title**: SEO-optimized, compelling title
        2. **Content Outline**: Detailed structure with H2/H3 headings
        3. **Key Points**: Main arguments and supporting evidence
        4. **Examples & Data**: Specific statistics, case studies, quotes to include
        5. **Target Keywords**: Primary and secondary SEO keywords
        6. **Call-to-Action**: Appropriate CTAs for the content
        7. **Estimated Length**: Recommended word count for comprehensive coverage

        Focus on creating a comprehensive plan that the content writer can execute.
        """
        
        try:
            response = await content_writer.arun(planning_prompt)
            
            return StepOutput(
                content=f"""
                ## Content Plan Ready

                **Blog Topic**: {topic}

                **Comprehensive Content Plan**:
                {response.content}

                **Research Integration**: {"✓ Research-based" if research_content else "✗ No research foundation"}
                **Status**: Ready for blog writing execution
                """.strip()
            )
        except Exception as e:
            return StepOutput(
                content=f"Content planning failed: {str(e)}",
                success=False,
            )
    
    async def seo_fact_check_integration_function(step_input: StepInput) -> StepOutput:
        """
        Integrate SEO optimization and fact-checking results
        """
        topic = step_input.input
        blog_content = step_input.previous_step_content
        
        integration_prompt = f"""
        BLOG POST INTEGRATION & FINAL OPTIMIZATION

        Original Topic: {topic}

        Blog Content:
        {blog_content[:1500] if blog_content else "No blog content available"}

        Please provide final integration including:
        1. **SEO Integration**: Apply SEO recommendations naturally
        2. **Fact Verification**: Incorporate fact-check results and corrections
        3. **Content Polish**: Final editorial review and enhancement
        4. **Quality Assurance**: Ensure all elements work together effectively
        5. **Publication Readiness**: Confirm blog is ready for publication

        Deliver the final, publication-ready blog post.
        """
        
        try:
            response = await content_writer.arun(integration_prompt)
            
            return StepOutput(
                content=f"""
                ## Final Blog Post Ready

                **Topic**: {topic}

                **Publication-Ready Blog**:
                {response.content}

                **Quality Indicators**:
                - SEO Optimized: ✓
                - Fact Checked: ✓
                - Content Quality: Professional
                - Status: Ready for Publication
                """.strip()
            )
        except Exception as e:
            return StepOutput(
                content=f"Final integration failed: {str(e)}",
                success=False,
            )
    
    # Condition evaluator for content quality
    def needs_additional_research(step_input: StepInput) -> bool:
        """
        Determine if additional research is needed based on content depth
        """
        content = step_input.previous_step_content or ""
        
        # Simple heuristic: check for research indicators
        research_indicators = [
            "research", "study", "data", "statistics", 
            "according to", "expert", "survey", "report"
        ]
        
        indicator_count = sum(1 for indicator in research_indicators if indicator.lower() in content.lower())
        content_length = len(content)
        
        # Need more research if content is short or lacks research depth
        return content_length < 1000 or indicator_count < 3
    
    # Define workflow steps
    topic_analysis_step = Step(
        name="Topic Analysis",
        executor=topic_analysis_function,
        description="Analyze blog topic and create research strategy",
    )
    
    research_step = Step(
        name="Research Execution", 
        team=research_team,
        description="Comprehensive research by specialized team",
    )
    
    content_planning_step = Step(
        name="Content Planning",
        executor=content_planning_function,
        description="Create detailed content plan based on research",
    )
    
    blog_writing_step = Step(
        name="Blog Writing",
        agent=content_writer,
        description="Write comprehensive blog post based on plan",
    )
    
    # Parallel optimization steps
    seo_optimization_step = Step(
        name="SEO Optimization",
        agent=seo_optimizer,
        description="Optimize blog content for search engines",
    )
    
    fact_checking_step = Step(
        name="Fact Checking",
        agent=fact_checker,
        description="Verify accuracy and credibility of content",
    )
    
    final_integration_step = Step(
        name="Final Integration",
        executor=seo_fact_check_integration_function,
        description="Integrate optimization and fact-check results",
    )
    
    # Additional research step for conditional execution
    additional_research_step = Step(
        name="Additional Research",
        team=research_team,
        description="Supplementary research for content enhancement",
    )
    
    return Workflow(
        id="comprehensive-blog-workflow",
        name="Comprehensive Blog Writing Workflow",
        description="End-to-end blog creation with research team, SEO optimization, and fact-checking",
        db=PostgresDb(
            id="blog-workflow-storage",
            db_url=db_url,
        ),
        steps=[
            # Phase 1: Analysis and Planning
            topic_analysis_step,
            
            # Phase 2: Research Execution
            research_step,
            
            # Phase 3: Content Planning
            content_planning_step,
            
            # Phase 4: Content Creation
            blog_writing_step,
            
            # Phase 5: Conditional Additional Research
            Condition(
                name="Additional Research Check",
                description="Determine if more research is needed",
                evaluator=needs_additional_research,
                steps=[additional_research_step],
            ),
            
            # Phase 6: Parallel Enhancement
            Parallel(
                seo_optimization_step,
                fact_checking_step,
                name="Content Enhancement",
                description="Parallel SEO optimization and fact-checking",
            ),
            
            # Phase 7: Final Integration
            final_integration_step,
        ],
    )


def get_simple_blog_workflow(debug_mode: bool = False) -> Workflow:
    """
    Simplified blog workflow for basic content creation
    
    Process Flow:
    1. Research (Research Team)
    2. Write (Content Writer)
    3. Optimize (SEO Optimizer)
    
    For users who want a faster, more basic blog creation process.
    """
    
    # Initialize agents
    research_team = get_research_team(debug_mode=debug_mode)
    content_writer = get_content_writer_agent(debug_mode=debug_mode)
    seo_optimizer = get_seo_optimizer_agent(debug_mode=debug_mode)
    
    # Define simple workflow steps
    simple_research_step = Step(
        name="Research",
        team=research_team,
        description="Research the blog topic comprehensively",
    )
    
    simple_writing_step = Step(
        name="Writing",
        agent=content_writer,
        description="Write blog post based on research",
    )
    
    simple_seo_step = Step(
        name="SEO Optimization",
        agent=seo_optimizer,
        description="Optimize blog for search engines",
    )
    
    return Workflow(
        id="simple-blog-workflow",
        name="Simple Blog Writing Workflow",
        description="Streamlined blog creation workflow",
        db=PostgresDb(
            id="simple-blog-workflow-storage", 
            db_url=db_url,
        ),
        steps=[
            simple_research_step,
            simple_writing_step,
            simple_seo_step,
        ],
    )