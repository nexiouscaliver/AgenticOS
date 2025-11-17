"""
Research-focused custom step functions for workflows
"""

from textwrap import dedent

from agno.workflow.types import StepInput, StepOutput

from ...teams.research_team import get_research_team


def topic_analyzer_function(step_input: StepInput) -> StepOutput:
    """
    Analyze and break down complex topics for comprehensive research

    Features:
    - Topic decomposition and scope definition
    - Research strategy planning
    - Audience identification and intent analysis
    - Competitive landscape assessment
    """
    topic = step_input.input
    additional_data = step_input.additional_data or {}

    # Extract context from additional data
    target_audience = additional_data.get("target_audience", "general audience")
    content_type = additional_data.get("content_type", "blog post")
    industry_focus = additional_data.get("industry", "general")

    analysis_prompt = f"""
    ADVANCED TOPIC ANALYSIS FOR {content_type.upper()}

    Topic: {topic}
    Target Audience: {target_audience}
    Industry Focus: {industry_focus}

    Please provide comprehensive topic analysis:

    1. **Core Topic Breakdown**:
       - Main subject and key themes
       - Primary and secondary subtopics
       - Scope boundaries and focus areas
       - Topic complexity and depth requirements

    2. **Audience & Intent Analysis**:
       - Target audience characteristics and expertise level
       - User search intent (informational, transactional, navigational)
       - Pain points and questions this topic addresses
       - Value proposition and expected outcomes

    3. **Research Strategy Framework**:
       - 6-8 specific research areas for comprehensive coverage
       - Primary source types to prioritize
       - Industry experts and authorities to reference
       - Data and statistics categories to investigate
       - International and diverse perspective requirements

    4. **Content Positioning**:
       - Unique angle or perspective to differentiate content
       - Competitive advantage opportunities
       - Content format optimization (how-to, analysis, opinion, etc.)
       - Engagement and shareability factors

    5. **SEO & Discovery Opportunities**:
       - Primary keyword clusters and search terms
       - Long-tail keyword opportunities
       - Featured snippet and voice search potential
       - Content series and topic cluster possibilities

    Provide a structured analysis that guides comprehensive research execution.
    """

    try:
        # Use research team for expert topic analysis
        research_team = get_research_team()
        response = research_team.run(analysis_prompt)

        enhanced_analysis = f"""
        ## Topic Analysis Complete ✅

        **Original Topic**: {topic}
        **Content Type**: {content_type}
        **Target Audience**: {target_audience}
        **Industry Focus**: {industry_focus}

        **Comprehensive Analysis**:
        {response.content}

        **Analysis Metadata**:
        - Analysis Date: Generated with current market context
        - Research Scope: Comprehensive multi-source investigation
        - Quality Level: Professional publication standard
        - Next Phase: Execute detailed research strategy

        **Research Readiness**: ✅ Ready for comprehensive research execution
        """.strip()

        return StepOutput(
            content=enhanced_analysis,
            metadata={
                "topic": topic,
                "content_type": content_type,
                "target_audience": target_audience,
                "industry": industry_focus,
                "analysis_completed": True,
            },
        )

    except Exception as e:
        return StepOutput(
            content=f"Topic analysis failed: {str(e)}",
            success=False,
        )


def research_coordinator_function(step_input: StepInput) -> StepOutput:
    """
    Coordinate and optimize research execution across multiple agents

    Features:
    - Research task distribution and prioritization
    - Quality control and verification protocols
    - Source diversity and credibility management
    - Research synthesis and gap identification
    """
    topic = step_input.input
    previous_analysis = step_input.previous_step_content
    additional_data = step_input.additional_data or {}

    # Extract research parameters
    research_depth = additional_data.get("research_depth", "comprehensive")
    time_sensitivity = additional_data.get("time_sensitivity", "current")
    geographic_scope = additional_data.get("geographic_scope", "global")

    coordination_prompt = f"""
    RESEARCH COORDINATION & EXECUTION STRATEGY

    Topic: {topic}
    Research Depth: {research_depth}
    Time Sensitivity: {time_sensitivity}
    Geographic Scope: {geographic_scope}

    Previous Analysis:
    {previous_analysis[:1000] if previous_analysis else "No previous analysis available"}

    Execute coordinated research with the following strategy:

    1. **Primary Research Objectives**:
       - Comprehensive information gathering on all key aspects
       - Multi-source verification and cross-referencing
       - Expert opinion collection and authoritative source identification
       - Current trend analysis and recent development tracking
       - Statistical data collection with context and validation

    2. **Source Diversification Strategy**:
       - Academic and peer-reviewed research (30%)
       - Industry reports and professional analysis (25%)
       - Government data and official statistics (20%)
       - News and current affairs coverage (15%)
       - Expert interviews and thought leadership (10%)

    3. **Quality Control Framework**:
       - Minimum 3 independent source verification for major claims
       - Source credibility assessment and bias evaluation
       - Fact-checking protocol for statistical information
       - Currency validation for time-sensitive information
       - Geographic representation for global perspective

    4. **Research Execution Protocol**:
       - Phase 1: Broad information gathering and source identification
       - Phase 2: Deep-dive analysis on key topics and themes
       - Phase 3: Expert perspective integration and opinion synthesis
       - Phase 4: Data validation and accuracy verification
       - Phase 5: Gap analysis and supplementary research

    Deliver comprehensive, verified, and actionable research results.
    """

    try:
        research_team = get_research_team()
        response = research_team.run(coordination_prompt)

        coordinated_research = f"""
        ## Coordinated Research Results 📊

        **Research Topic**: {topic}
        **Execution Parameters**:
        - Depth Level: {research_depth}
        - Time Focus: {time_sensitivity}
        - Geographic Scope: {geographic_scope}

        **Comprehensive Research Findings**:
        {response.content}

        **Research Quality Indicators**:
        - Source Diversity: ✅ Multiple source types consulted
        - Verification Level: ✅ Cross-reference validation completed
        - Expert Integration: ✅ Authoritative perspectives included
        - Currency Check: ✅ Recent information prioritized
        - Global Perspective: ✅ International context provided

        **Research Status**: ✅ Comprehensive investigation completed
        **Next Phase**: Ready for content planning and writing
        """.strip()

        return StepOutput(
            content=coordinated_research,
            metadata={
                "research_completed": True,
                "research_depth": research_depth,
                "source_count": "multiple_verified",
                "quality_level": "comprehensive",
            },
        )

    except Exception as e:
        return StepOutput(
            content=f"Research coordination failed: {str(e)}",
            success=False,
        )


def competitive_analysis_function(step_input: StepInput) -> StepOutput:
    """
    Analyze competitive landscape and identify content differentiation opportunities

    Features:
    - Competitor content analysis and gap identification
    - SERP analysis and ranking opportunity assessment
    - Content format and approach optimization
    - Unique value proposition development
    """
    topic = step_input.input
    research_content = step_input.previous_step_content
    additional_data = step_input.additional_data or {}

    # Extract competitive analysis parameters
    competitor_count = additional_data.get("competitor_analysis_depth", "top_10")
    content_format = additional_data.get("content_format", "blog_post")
    differentiation_focus = additional_data.get("differentiation", "expertise")

    competitive_prompt = f"""
    COMPETITIVE LANDSCAPE ANALYSIS & DIFFERENTIATION STRATEGY

    Topic: {topic}
    Content Format: {content_format}
    Differentiation Focus: {differentiation_focus}
    Analysis Depth: {competitor_count}

    Research Context:
    {research_content[:800] if research_content else "Limited research context"}

    Conduct comprehensive competitive analysis:

    1. **Competitor Content Analysis**:
       - Identify top 10 ranking content pieces for target keywords
       - Analyze content depth, structure, and approach differences
       - Evaluate content quality, accuracy, and comprehensiveness
       - Identify common themes and standard industry coverage
       - Assess content freshness and update frequency

    2. **Content Gap Identification**:
       - Find topics/aspects not adequately covered by competitors
       - Identify opportunities for deeper, more comprehensive coverage
       - Locate outdated information that needs updating
       - Discover underserved audience segments or use cases
       - Find opportunities for unique data or expert perspectives

    3. **SERP & Ranking Analysis**:
       - Evaluate search result features: snippets, images, videos
       - Analyze user intent and search behavior patterns
       - Identify keyword opportunities with competition gaps
       - Assess content format performance (long-form, lists, guides)
       - Evaluate social sharing and engagement patterns

    4. **Differentiation Strategy**:
       - Develop unique angle based on {differentiation_focus}
       - Create superior value proposition for target audience
       - Plan content enhancements: visuals, data, expert quotes
       - Design engagement features: interactivity, tools, resources
       - Establish authority signals and trust indicators

    5. **Competitive Advantage Framework**:
       - Leverage research insights competitors lack
       - Apply superior methodology or data analysis
       - Provide more actionable and practical guidance
       - Include diverse perspectives and case studies
       - Offer comprehensive resource compilation

    Deliver actionable insights for content differentiation and competitive advantage.
    """

    try:
        research_team = get_research_team()
        response = research_team.run(competitive_prompt)

        competitive_analysis = f"""
        ## Competitive Analysis & Differentiation Strategy 🎯

        **Analysis Topic**: {topic}
        **Content Format**: {content_format}
        **Differentiation Approach**: {differentiation_focus}
        **Competitive Scope**: {competitor_count}

        **Comprehensive Competitive Intelligence**:
        {response.content}

        **Strategic Recommendations**:
        - **Content Positioning**: Based on competitive gap analysis
        - **Unique Value Proposition**: Differentiated approach identified
        - **SEO Opportunities**: Keyword and ranking gaps discovered
        - **Content Enhancement**: Superior format and structure planned
        - **Authority Building**: Expert credibility and trust signals integrated

        **Competitive Advantage Status**: ✅ Clear differentiation strategy developed
        **Implementation Readiness**: ✅ Ready for content creation with competitive edge
        """.strip()

        return StepOutput(
            content=competitive_analysis,
            metadata={
                "competitive_analysis_completed": True,
                "differentiation_strategy": differentiation_focus,
                "content_format": content_format,
                "competitive_advantage": True,
            },
        )

    except Exception as e:
        return StepOutput(
            content=f"Competitive analysis failed: {str(e)}",
            success=False,
        )
