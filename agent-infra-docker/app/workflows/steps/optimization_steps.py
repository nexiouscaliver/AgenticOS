"""
SEO and quality optimization custom step functions for workflows
"""

from textwrap import dedent
from agno.workflow.types import StepInput, StepOutput
from ...agents.seo_optimizer import get_seo_optimizer_agent
from ...agents.fact_checker import get_fact_checker_agent


def seo_analyzer_function(step_input: StepInput) -> StepOutput:
    """
    Comprehensive SEO analysis and optimization recommendations
    """
    topic = step_input.input
    content = step_input.previous_step_content
    additional_data = step_input.additional_data or {}
    
    seo_focus = additional_data.get("seo_priority", "balanced")
    target_keywords = additional_data.get("keywords", [])
    
    seo_prompt = f"""
    COMPREHENSIVE SEO ANALYSIS & OPTIMIZATION

    Content Topic: {topic}
    SEO Focus: {seo_focus}
    Target Keywords: {target_keywords}

    Content to Analyze:
    {content[:1500] if content else "No content provided"}

    Provide comprehensive SEO analysis and optimization recommendations:

    1. **Current SEO Assessment**:
       - Keyword usage and density analysis
       - Title and meta description evaluation
       - Header structure and hierarchy review
       - Content length and depth assessment
       - Internal/external linking opportunities

    2. **Optimization Recommendations**:
       - Primary keyword integration improvements
       - Long-tail keyword opportunities
       - Featured snippet optimization potential
       - Voice search optimization suggestions
       - Local SEO considerations (if applicable)

    3. **Technical SEO Enhancements**:
       - URL structure optimization
       - Schema markup recommendations
       - Image SEO and alt text suggestions
       - Mobile optimization considerations
       - Page speed impact factors

    Provide actionable SEO improvements for better search performance.
    """
    
    try:
        seo_optimizer = get_seo_optimizer_agent()
        response = seo_optimizer.run(seo_prompt)
        
        return StepOutput(
            content=f"## SEO Analysis Complete\n\n{response.content}",
            metadata={"seo_analyzed": True, "recommendations_provided": True}
        )
    except Exception as e:
        return StepOutput(content=f"SEO analysis failed: {str(e)}", success=False)


def fact_verifier_function(step_input: StepInput) -> StepOutput:
    """
    Comprehensive fact-checking and accuracy verification
    """
    topic = step_input.input
    content = step_input.previous_step_content
    additional_data = step_input.additional_data or {}
    
    verification_level = additional_data.get("verification_level", "comprehensive")
    
    fact_check_prompt = f"""
    COMPREHENSIVE FACT VERIFICATION

    Content Topic: {topic}
    Verification Level: {verification_level}

    Content to Verify:
    {content[:1500] if content else "No content provided"}

    Perform comprehensive fact-checking:

    1. **Claim Identification**: Extract all verifiable factual claims
    2. **Source Verification**: Check accuracy of cited sources
    3. **Statistical Validation**: Verify numbers, percentages, and data
    4. **Attribution Check**: Confirm quotes and attributions
    5. **Currency Assessment**: Validate timeliness of information

    Provide verification results with confidence scores.
    """
    
    try:
        fact_checker = get_fact_checker_agent()
        response = fact_checker.run(fact_check_prompt)
        
        return StepOutput(
            content=f"## Fact Verification Complete\n\n{response.content}",
            metadata={"fact_checked": True, "verification_completed": True}
        )
    except Exception as e:
        return StepOutput(content=f"Fact checking failed: {str(e)}", success=False)


def quality_assessor_function(step_input: StepInput) -> StepOutput:
    """
    Overall content quality assessment and improvement recommendations
    """
    topic = step_input.input
    content = step_input.previous_step_content
    additional_data = step_input.additional_data or {}
    
    quality_standards = additional_data.get("quality_level", "professional")
    
    quality_prompt = f"""
    COMPREHENSIVE QUALITY ASSESSMENT

    Content Topic: {topic}
    Quality Standards: {quality_standards}

    Content to Assess:
    {content[:1000] if content else "No content provided"}

    Provide comprehensive quality assessment:

    1. **Content Quality Metrics**:
       - Clarity and readability assessment
       - Depth and comprehensiveness evaluation
       - Accuracy and credibility review
       - Engagement and value delivery analysis

    2. **Improvement Recommendations**:
       - Content enhancement opportunities
       - Structure and flow optimization
       - Reader experience improvements
       - Authority and trust building

    Rate overall quality and provide specific improvement suggestions.
    """
    
    try:
        # Use content writer for quality assessment
        from ...agents.content_writer import get_content_writer_agent
        quality_assessor = get_content_writer_agent()
        response = quality_assessor.run(quality_prompt)
        
        return StepOutput(
            content=f"## Quality Assessment Complete\n\n{response.content}",
            metadata={"quality_assessed": True, "improvement_suggestions": True}
        )
    except Exception as e:
        return StepOutput(content=f"Quality assessment failed: {str(e)}", success=False)