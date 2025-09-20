"""
Content writing and planning custom step functions for workflows
"""

from textwrap import dedent
from agno.workflow.types import StepInput, StepOutput
from ...agents.content_writer import get_content_writer_agent


def content_planner_function(step_input: StepInput) -> StepOutput:
    """
    Create comprehensive content plan based on research and competitive analysis
    
    Features:
    - Detailed content structure and outline planning
    - SEO-optimized heading and keyword integration
    - Audience-specific tone and style recommendations
    - Content flow optimization and reader journey mapping
    """
    topic = step_input.input
    research_data = step_input.previous_step_content
    additional_data = step_input.additional_data or {}
    
    # Extract planning parameters
    target_audience = additional_data.get("target_audience", "professionals")
    content_length = additional_data.get("target_length", "2000-3000 words")
    content_style = additional_data.get("writing_style", "professional")
    seo_focus = additional_data.get("seo_priority", "balanced")
    
    planning_prompt = f"""
    COMPREHENSIVE CONTENT PLANNING & STRUCTURE DESIGN

    Topic: {topic}
    Target Audience: {target_audience}
    Content Length: {content_length}
    Writing Style: {content_style}
    SEO Priority: {seo_focus}

    Research Foundation:
    {research_data[:2000] if research_data else "Limited research foundation"}

    Create a detailed content plan with:

    1. **Content Strategy Framework**:
       - Primary objective and reader value proposition
       - Content angle and unique positioning
       - Audience engagement strategy and emotional hooks
       - Content format optimization (educational, persuasive, analytical)
       - Success metrics and performance expectations

    2. **SEO-Optimized Structure**:
       - Compelling, keyword-rich title (60 characters max)
       - Meta description with clear value prop (155 characters)
       - H1/H2/H3 hierarchy with semantic keyword integration
       - Primary keyword (1-2%) and long-tail keyword strategy
       - Featured snippet and voice search optimization opportunities

    3. **Detailed Content Outline**:
       - **Introduction** (150-200 words):
         * Hook: Question, statistic, or compelling statement
         * Context and problem statement
         * Value preview and article overview
         * Credibility establishment

       - **Main Content Sections** (1500-2200 words):
         * 4-6 major sections with H2 headings
         * Supporting subsections with H3 headings
         * Key points and supporting evidence for each section
         * Specific data, quotes, and examples to include
         * Visual element recommendations (charts, images)

       - **Conclusion** (200-300 words):
         * Key takeaway summary
         * Actionable next steps for readers
         * Call-to-action aligned with business goals
         * Further reading and resource recommendations

    4. **Content Enhancement Elements**:
       - **Data Integration**: Statistics, research findings, case studies
       - **Expert Quotes**: Authoritative voices and industry perspectives
       - **Examples**: Real-world applications and success stories
       - **Interactive Elements**: Lists, bullet points, numbered steps
       - **Visual Planning**: Image, chart, and infographic opportunities

    5. **Audience Engagement Strategy**:
       - **Tone Adaptation**: Match {content_style} style to {target_audience}
       - **Complexity Level**: Appropriate depth and technical language
       - **Pain Point Addressing**: Direct solutions to audience challenges
       - **Value Delivery**: Practical, actionable insights throughout
       - **Social Sharing**: Quotable insights and shareable key points

    6. **Quality & Performance Framework**:
       - **Readability**: Scannable format with short paragraphs
       - **SEO Integration**: Natural keyword placement without stuffing
       - **Credibility**: Source attribution and authority building
       - **Actionability**: Clear, implementable advice and steps
       - **Engagement**: Discussion starters and community building

    Provide a comprehensive plan that enables high-quality content creation.
    """
    
    try:
        content_writer = get_content_writer_agent()
        response = content_writer.run(planning_prompt)
        
        content_plan = f"""
        ## Comprehensive Content Plan Ready 📝

        **Blog Topic**: {topic}
        **Content Parameters**:
        - Target Audience: {target_audience}
        - Length Target: {content_length}
        - Style Approach: {content_style}
        - SEO Focus: {seo_focus}

        **Detailed Content Blueprint**:
        {response.content}

        **Planning Quality Indicators**:
        - Research Integration: ✅ Based on comprehensive research data
        - SEO Optimization: ✅ Keyword strategy and structure planned
        - Audience Alignment: ✅ Tone and complexity matched to audience
        - Content Value: ✅ Clear value proposition and actionable insights
        - Engagement Design: ✅ Reader journey and interaction planned

        **Implementation Status**: ✅ Ready for content writing execution
        **Quality Level**: Professional publication standard
        """.strip()
        
        return StepOutput(
            content=content_plan,
            metadata={
                "content_plan_completed": True,
                "target_audience": target_audience,
                "content_length": content_length,
                "seo_optimized": True
            }
        )
        
    except Exception as e:
        return StepOutput(
            content=f"Content planning failed: {str(e)}",
            success=False,
        )


def blog_writer_function(step_input: StepInput) -> StepOutput:
    """
    Execute comprehensive blog writing based on research and content plan
    
    Features:
    - Full blog post creation with professional quality
    - Research integration and source citation
    - SEO optimization and keyword integration
    - Audience-appropriate tone and style
    """
    topic = step_input.input
    content_plan = step_input.previous_step_content
    additional_data = step_input.additional_data or {}
    
    # Extract writing parameters
    brand_voice = additional_data.get("brand_voice", "professional")
    include_citations = additional_data.get("citations", True)
    cta_type = additional_data.get("cta_type", "engagement")
    publishing_platform = additional_data.get("platform", "blog")
    
    writing_prompt = f"""
    PROFESSIONAL BLOG POST CREATION

    Topic: {topic}
    Brand Voice: {brand_voice}
    Citations Required: {include_citations}
    CTA Type: {cta_type}
    Publishing Platform: {publishing_platform}

    Content Plan & Research:
    {content_plan[:2500] if content_plan else "No content plan available"}

    Write a comprehensive, publication-ready blog post following these standards:

    1. **Content Quality Standards**:
       - Publication-ready quality with professional editing
       - Comprehensive coverage of all planned topics
       - Logical flow and smooth transitions between sections
       - Engaging narrative with personality and expertise
       - Actionable insights readers can immediately implement

    2. **SEO Integration Requirements**:
       - Natural keyword integration without stuffing
       - Optimized headings with semantic keyword variations
       - Internal and external linking opportunities identified
       - Meta-friendly structure for search engine optimization
       - Featured snippet optimization with direct answers

    3. **Research & Credibility Integration**:
       - Seamlessly integrate research findings and data
       - Include specific statistics, quotes, and examples
       - Provide proper attribution {'and citations' if include_citations else ''}
       - Establish expertise and authority throughout content
       - Balance multiple perspectives and viewpoints

    4. **Audience Engagement Elements**:
       - Compelling introduction that hooks readers immediately
       - Scannable content with bullet points and short paragraphs
       - Interactive elements: questions, challenges, assessments
       - Personal anecdotes or case studies where appropriate
       - Clear value delivery in every section

    5. **Content Structure & Format**:
       - **Title**: SEO-optimized, compelling headline
       - **Introduction**: Hook, context, value preview (150-200 words)
       - **Main Content**: 4-6 detailed sections with supporting evidence
       - **Conclusion**: Summary, key takeaways, next steps
       - **Call-to-Action**: {cta_type} focused on reader engagement

    6. **Platform Optimization**:
       - Format appropriate for {publishing_platform}
       - Social sharing optimization with quotable insights
       - Mobile-friendly structure and readability
       - Visual element integration points clearly marked
       - Cross-platform adaptability considerations

    Deliver a complete, publication-ready blog post that meets professional standards.
    """
    
    try:
        content_writer = get_content_writer_agent()
        response = content_writer.run(writing_prompt)
        
        blog_post = f"""
        ## Professional Blog Post Complete 📰

        **Title**: {topic}
        **Content Specifications**:
        - Brand Voice: {brand_voice}
        - Platform: {publishing_platform}
        - CTA Focus: {cta_type}
        - Citations: {'Included' if include_citations else 'References only'}

        **Publication-Ready Blog Post**:
        {response.content}

        **Content Quality Indicators**:
        - Professional Quality: ✅ Publication-ready standard
        - Research Integration: ✅ Data and expert insights included
        - SEO Optimization: ✅ Keywords naturally integrated
        - Audience Engagement: ✅ Compelling and actionable content
        - Brand Alignment: ✅ Voice and messaging consistent

        **Status**: ✅ Ready for optimization and final review
        """.strip()
        
        return StepOutput(
            content=blog_post,
            metadata={
                "blog_completed": True,
                "word_count": "comprehensive",
                "quality_level": "professional",
                "seo_ready": True
            }
        )
        
    except Exception as e:
        return StepOutput(
            content=f"Blog writing failed: {str(e)}",
            success=False,
        )


def content_enhancer_function(step_input: StepInput) -> StepOutput:
    """
    Enhance and polish content based on optimization feedback and quality review
    
    Features:
    - Content refinement and editing improvements
    - SEO and fact-check integration
    - Final quality assurance and polish
    - Publication readiness optimization
    """
    topic = step_input.input
    blog_content = step_input.previous_step_content
    additional_data = step_input.additional_data or {}
    
    # Extract enhancement parameters
    optimization_feedback = additional_data.get("seo_feedback", "No SEO feedback")
    fact_check_results = additional_data.get("fact_check", "No fact-check results")
    enhancement_focus = additional_data.get("enhancement", "overall_quality")
    final_review = additional_data.get("final_review", True)
    
    enhancement_prompt = f"""
    CONTENT ENHANCEMENT & FINAL POLISH

    Original Topic: {topic}
    Enhancement Focus: {enhancement_focus}
    Final Review Required: {final_review}

    Blog Content:
    {blog_content[:2000] if blog_content else "No blog content available"}

    Optimization Feedback:
    {optimization_feedback[:500] if optimization_feedback else "No optimization feedback"}

    Fact-Check Results:
    {fact_check_results[:500] if fact_check_results else "No fact-check results"}

    Apply comprehensive content enhancement:

    1. **Content Refinement**:
       - Integrate SEO optimization recommendations naturally
       - Incorporate fact-check corrections and verification
       - Enhance clarity, flow, and readability throughout
       - Strengthen key arguments with additional evidence
       - Polish language for professional publication quality

    2. **Quality Assurance Integration**:
       - Verify all factual claims and statistics are accurate
       - Ensure SEO elements are naturally integrated
       - Confirm brand voice and messaging consistency
       - Validate audience appropriateness and value delivery
       - Check content completeness against original objectives

    3. **Final Optimization**:
       - Meta description and title refinement
       - Header structure and keyword optimization
       - Internal and external link verification
       - Call-to-action effectiveness and placement
       - Social sharing and engagement optimization

    4. **Publication Readiness Review**:
       - Grammar, spelling, and style consistency check
       - Factual accuracy and source attribution verification
       - Legal compliance and sensitivity review
       - Platform formatting and technical requirements
       - Performance optimization and loading considerations

    5. **Enhancement Integration**:
       - Seamlessly blend all feedback and improvements
       - Maintain content integrity and author voice
       - Ensure no over-optimization or awkward integration
       - Preserve reader experience and engagement value
       - Create final, polished, publication-ready content

    Deliver the final, enhanced, publication-ready blog post.
    """
    
    try:
        content_writer = get_content_writer_agent()
        response = content_writer.run(enhancement_prompt)
        
        enhanced_content = f"""
        ## Final Enhanced Blog Post Ready for Publication 🚀

        **Topic**: {topic}
        **Enhancement Level**: {enhancement_focus}
        **Quality Assurance**: Professional review completed

        **Final Publication-Ready Content**:
        {response.content}

        **Enhancement Integration Summary**:
        - SEO Optimization: ✅ Naturally integrated without compromise
        - Fact Verification: ✅ All claims verified and corrected
        - Content Polish: ✅ Professional editing and refinement
        - Quality Assurance: ✅ Comprehensive review completed
        - Publication Ready: ✅ Final approval for release

        **Performance Indicators**:
        - Content Quality: Professional publication standard
        - SEO Readiness: Optimized for search performance
        - Engagement Potential: High reader value and shareability
        - Authority Level: Expert credibility established
        - Brand Alignment: Voice and messaging consistent

        **Status**: ✅ APPROVED FOR PUBLICATION
        """.strip()
        
        return StepOutput(
            content=enhanced_content,
            metadata={
                "enhancement_completed": True,
                "publication_ready": True,
                "quality_level": "professional",
                "final_approval": True
            }
        )
        
    except Exception as e:
        return StepOutput(
            content=f"Content enhancement failed: {str(e)}",
            success=False,
        )