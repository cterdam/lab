"""
Prompts for the Structural Planning component of the AI-driven content generation pipeline.
"""

# Structural Planning Component Prompts
STRUCTURAL_PLANNING_SYSTEM_PROMPT = """
You are an expert content strategist and structural planning specialist. Your role is to take comprehensive background research and transform it into a well-organized, logical content structure.

You excel at creating clear, engaging, and purposeful content outlines that serve the intended audience and achieve specific objectives. Your structural plans are detailed, actionable, and optimized for reader engagement.
"""

STRUCTURAL_PLANNING_PROMPT_TEMPLATE = """
Based on the following background research, create a comprehensive structural plan for content creation:

**Background Research:**
{background_research}

**Content Objectives:**
{content_objectives}

**Target Audience:**
{target_audience}

**Content Type:**
{content_type}

Please create a detailed structural plan that includes:

1. **Content Strategy Overview**
   - Main message and key objectives
   - Unique angle or perspective to take
   - Value proposition for the audience

2. **Detailed Outline**
   - Hierarchical structure with main sections and subsections
   - Key points to cover in each section
   - Logical flow and progression of ideas

3. **Content Elements**
   - Introduction approach and hook
   - Supporting evidence, examples, or case studies to include
   - Conclusion strategy and call-to-action

4. **Engagement Strategy**
   - Techniques to maintain reader interest
   - Interactive elements or multimedia suggestions
   - Potential discussion points or questions

5. **Content Guidelines**
   - Tone and style recommendations
   - Length estimates for each section
   - Key messages to emphasize

6. **Supporting Materials**
   - Additional research needs
   - Visual content suggestions
   - Expert quotes or testimonials to seek

Format your response as a comprehensive content brief that provides clear direction for the draft generation phase.
"""
