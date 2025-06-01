"""
Beautiful UI for AI Content Generation Pipeline

A modern, intuitive interface for the three-agent content generation system:
- Discovery Agent: Discovers engaging questions and content angles
- Planning Agent: Creates structural content plans
- Writer Agent: Generates the final content

Features:
- Real-time progress tracking
- Beautiful markdown rendering
- Token usage analytics
- Responsive design
- Async execution for best performance
"""

import asyncio
import os
import traceback
from datetime import datetime
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Try to import the content generation components
try:
    from src.lib.model.txt.api.openai import OpenaiLm, OpenaiLmInitParams
    from src.task.content_generation.pipeline import (
        ContentGenerationPipeline,
        ContentGenerationPipelineParams,
        ContentGenerationPipelineResult,
    )

    IMPORTS_SUCCESS = True
    IMPORT_ERROR = None
except Exception as e:
    IMPORTS_SUCCESS = False
    IMPORT_ERROR = str(e)

    # Create placeholder classes for UI testing
    class OpenaiLm:
        pass

    class OpenaiLmInitParams:
        pass

    class ContentGenerationPipeline:
        pass

    class ContentGenerationPipelineParams:
        pass

    class ContentGenerationPipelineResult:
        pass


# Configure Streamlit page
st.set_page_config(
    page_title="AI Content Generation Studio",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for beautiful styling
st.markdown(
    """
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .agent-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .agent-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .agent-icon {
        font-size: 2rem;
        margin-right: 0.5rem;
    }
    
    .token-metric {
        background: #f0f2f6;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .markdown-content {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        max-height: 400px;
        overflow-y: auto;
    }
    
    .progress-container {
        margin: 2rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session_state():
    """Initialize session state variables."""
    if "generation_result" not in st.session_state:
        st.session_state.generation_result = None
    if "is_generating" not in st.session_state:
        st.session_state.is_generating = False
    if "generation_progress" not in st.session_state:
        st.session_state.generation_progress = 0


def render_header():
    """Render the main header."""
    st.markdown(
        """
    <div class="main-header">
        <h1>🚀 AI Content Generation Studio</h1>
        <p>Transform your ideas into engaging content with our multi-agent AI system</p>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_error_message():
    """Render an error message if imports failed."""
    st.markdown(
        f"""
    <div class="error-box">
        <h3>⚠️ Configuration Error</h3>
        <p>There was an issue loading the content generation components.</p>
        <details>
            <summary>Error Details</summary>
            <pre>{IMPORT_ERROR}</pre>
        </details>
        <p><strong>Possible solutions:</strong></p>
        <ul>
            <li>Make sure you're running from the project root directory</li>
            <li>Check that all dependencies are installed: <code>pip install -r requirements.txt</code></li>
            <li>Verify your OpenAI API key is set: <code>export OPENAI_API_KEY="your-key"</code></li>
            <li>Try running the basic demo first: <code>python -m src.task.content_generation.test_pipeline</code></li>
        </ul>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_agent_card(icon: str, title: str, description: str, status: str = "Ready"):
    """Render an agent status card."""
    status_color = {
        "Ready": "#28a745",
        "Running": "#ffc107",
        "Complete": "#007bff",
        "Error": "#dc3545",
    }

    st.markdown(
        f"""
    <div class="agent-card">
        <div class="agent-header">
            <span class="agent-icon">{icon}</span>
            <div>
                <h3>{title}</h3>
                <p style="margin: 0; color: #666;">{description}</p>
                <small style="color: {status_color.get(status, '#666')};">Status: {status}</small>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render the sidebar with input form."""
    st.sidebar.header("📝 Content Generation Settings")

    # Basic inputs
    st.sidebar.subheader("📍 Topic & Keywords")
    field_of_topic = st.sidebar.text_input(
        "Field of Topic",
        value="Technology",
        help="The main field or domain for your content",
        placeholder="e.g., Technology, Health, Finance",
    )

    keywords = st.sidebar.text_area(
        "Keywords",
        value="future of work automation, artificial intelligence",
        help="Keywords or phrases related to your topic",
        placeholder="e.g., AI, machine learning, automation, jobs",
    )

    # Advanced settings
    st.sidebar.subheader("🎯 Content Configuration")

    content_objectives = st.sidebar.text_area(
        "Content Objectives",
        value="Create engaging, informative content that educates and engages the target audience",
        help="What do you want to achieve with this content?",
    )

    target_audience = st.sidebar.selectbox(
        "Target Audience",
        [
            "General audience with interest in the topic",
            "Business professionals and executives",
            "Students and academics",
            "Technical specialists",
            "Health-conscious individuals",
            "Financial enthusiasts",
            "Creative professionals",
        ],
    )

    content_type = st.sidebar.selectbox(
        "Content Type",
        [
            "Article/Blog Post",
            "Professional article",
            "Educational guide",
            "Opinion piece",
            "How-to guide",
            "Case study",
            "Research summary",
        ],
    )

    additional_instructions = st.sidebar.text_area(
        "Additional Instructions",
        value="Focus on practical insights and actionable information. Make it engaging and easy to read.",
        help="Any specific requirements or style preferences",
    )

    # Advanced parameters
    with st.sidebar.expander("⚙️ Advanced Settings"):
        discovery_max_tokens = st.slider("Discovery Max Tokens", 1000, 3000, 2000)
        planning_max_tokens = st.slider("Planning Max Tokens", 1000, 4000, 3000)
        generation_max_tokens = st.slider("Generation Max Tokens", 2000, 10000, 7000)

        discovery_temperature = st.slider("Discovery Creativity", 0.0, 1.0, 0.7, 0.9)
        planning_temperature = st.slider("Planning Creativity", 0.0, 1.0, 0.4, 0.1)
        generation_temperature = st.slider("Generation Creativity", 0.0, 1.0, 0.6, 0.4)

    return {
        "field_of_topic": field_of_topic,
        "keywords": keywords,
        "content_objectives": content_objectives,
        "target_audience": target_audience,
        "content_type": content_type,
        "additional_instructions": additional_instructions,
        "discovery_max_tokens": discovery_max_tokens,
        "planning_max_tokens": planning_max_tokens,
        "generation_max_tokens": generation_max_tokens,
        "discovery_temperature": discovery_temperature,
        "planning_temperature": planning_temperature,
        "generation_temperature": generation_temperature,
    }


async def generate_content_async(
    params: dict,
) -> Optional[ContentGenerationPipelineResult]:
    """Generate content asynchronously with progress updates."""
    if not IMPORTS_SUCCESS:
        st.error(
            "Cannot generate content due to import errors. Please check the configuration."
        )
        return None

    try:
        # Initialize the model
        model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))
        pipeline = ContentGenerationPipeline(model)

        # Create pipeline parameters
        pipeline_params = ContentGenerationPipelineParams(**params)

        # Generate content asynchronously
        result = await pipeline.agenerate_content(pipeline_params)
        return result

    except Exception as e:
        st.error(f"Error generating content: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None


def render_demo_content():
    """Render demo content when the system isn't working."""
    st.subheader("📖 Demo Content")

    demo_content = """
# The Future of Artificial Intelligence in the Workplace

## Introduction

Artificial Intelligence (AI) is rapidly transforming the modern workplace, bringing both opportunities and challenges that will reshape how we work, collaborate, and create value in the coming decades.

## Key Areas of Impact

### 1. Automation and Job Evolution
- **Routine Task Automation**: AI is automating repetitive tasks, freeing humans for more creative work
- **Job Transformation**: Rather than simply replacing jobs, AI is changing how jobs are performed
- **New Role Creation**: Emerging positions in AI management, data science, and human-AI collaboration

### 2. Enhanced Decision Making
- **Data-Driven Insights**: AI processes vast amounts of data to provide actionable insights
- **Predictive Analytics**: Forecasting trends and outcomes to improve strategic planning
- **Real-Time Optimization**: Continuous improvement of processes and workflows

### 3. Improved Collaboration
- **Intelligent Assistants**: AI-powered tools that enhance human capabilities
- **Cross-Team Communication**: Breaking down silos through intelligent information sharing
- **Global Collaboration**: AI translation and cultural adaptation tools

## Challenges and Considerations

### Ethical Implications
- Ensuring fairness and avoiding bias in AI systems
- Maintaining transparency in AI decision-making
- Protecting employee privacy and data rights

### Workforce Adaptation
- Reskilling and upskilling programs
- Managing the transition period
- Supporting displaced workers

## Conclusion

The integration of AI in the workplace represents a fundamental shift that requires thoughtful planning, ethical consideration, and proactive adaptation. Organizations that embrace this change while prioritizing human welfare will be best positioned for future success.
    """

    st.markdown(demo_content)

    st.info(
        "👆 This is demo content. When the system is properly configured, you'll see your generated content here!"
    )


def render_demo_analytics():
    """Render demo analytics when the system isn't working."""
    st.subheader("📊 Demo Token Analytics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Input", "1,250")

    with col2:
        st.metric("Total Output", "3,890")

    with col3:
        st.metric("Total Tokens", "5,140")

    with col4:
        st.metric("Est. Cost", "$0.0078")

    # Demo chart
    try:
        import pandas as pd
        import plotly.express as px

        token_data = pd.DataFrame(
            {
                "Component": ["Discovery Agent", "Planning Agent", "Writer Agent"],
                "Input Tokens": [420, 380, 450],
                "Output Tokens": [680, 590, 2620],
            }
        )

        fig = px.bar(
            token_data,
            x="Component",
            y=["Input Tokens", "Output Tokens"],
            title="Demo Token Usage by Component",
            color_discrete_map={"Input Tokens": "#3498db", "Output Tokens": "#e74c3c"},
        )
        fig.update_layout(barmode="stack")
        st.plotly_chart(fig, use_container_width=True)
    except ImportError:
        st.info("Install plotly to see the token usage chart")


def main():
    """Main application function."""
    init_session_state()
    render_header()

    # Check if imports were successful
    if not IMPORTS_SUCCESS:
        render_error_message()

        st.markdown("---")
        st.subheader("🎮 Demo Mode")
        st.info(
            "Since the system isn't configured, here's what the UI would look like with generated content:"
        )

        # Show demo content
        render_demo_content()
        st.markdown("---")
        render_demo_analytics()

        return

    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.warning(
            "⚠️ OpenAI API key not found! Please set your OPENAI_API_KEY environment variable."
        )
        st.info("Create a `.env` file with: `OPENAI_API_KEY=your-key-here`")

    # Sidebar with inputs
    params = render_sidebar()

    # Main content area
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🤖 Agents")

        # Agent status cards
        if st.session_state.is_generating:
            render_agent_card(
                "🔍",
                "Discovery Agent",
                "Analyzing keywords and discovering engaging angles",
                "Running",
            )
            render_agent_card(
                "📋",
                "Planning Agent",
                "Creating content structure and strategy",
                "Ready",
            )
            render_agent_card(
                "✍️", "Writer Agent", "Generating final content draft", "Ready"
            )
        else:
            render_agent_card(
                "🔍",
                "Discovery Agent",
                "Analyzes keywords and discovers engaging angles",
                "Ready",
            )
            render_agent_card(
                "📋",
                "Planning Agent",
                "Creates content structure and strategy",
                "Ready",
            )
            render_agent_card(
                "✍️", "Writer Agent", "Generates final content draft", "Ready"
            )

    with col2:
        st.subheader("🎮 Controls")

        # Validation
        if not params["field_of_topic"].strip():
            st.warning("⚠️ Please enter a field of topic")
            generate_disabled = True
        elif not params["keywords"].strip():
            st.warning("⚠️ Please enter some keywords")
            generate_disabled = True
        elif not os.getenv("OPENAI_API_KEY"):
            st.warning("⚠️ OpenAI API key required")
            generate_disabled = True
        else:
            generate_disabled = False

        # Generate button
        if st.button(
            "🚀 Generate Content",
            disabled=generate_disabled or st.session_state.is_generating,
            use_container_width=True,
            type="primary",
        ):
            st.session_state.is_generating = True
            st.rerun()

    # Handle content generation
    if st.session_state.is_generating and st.session_state.generation_result is None:
        with st.container():
            st.info("🔄 Generating content... This may take a few moments.")

            try:
                # Run async generation
                result = asyncio.run(generate_content_async(params))

                if result:
                    st.session_state.generation_result = result
                    st.success("✅ Content generation completed!")
                else:
                    st.error("❌ Content generation failed.")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.error(f"Traceback: {traceback.format_exc()}")

            finally:
                st.session_state.is_generating = False
                st.rerun()

    # Display results or demo
    if st.session_state.generation_result:
        result = st.session_state.generation_result

        st.markdown("---")

        # Component results
        st.subheader("🔧 Component Results")

        with st.expander("🔍 Discovery Agent Results", expanded=False):
            st.markdown(result.discovery_result.interest_analysis)
            st.metric(
                "Tokens",
                f"{result.discovery_result.input_tokens} → {result.discovery_result.output_tokens}",
            )

        with st.expander("📋 Planning Agent Results", expanded=False):
            st.markdown(result.planning_result.structural_plan)
            st.metric(
                "Tokens",
                f"{result.planning_result.input_tokens} → {result.planning_result.output_tokens}",
            )

        with st.expander("✍️ Writer Agent Results", expanded=False):
            st.markdown(result.generation_result.content_draft)
            st.metric(
                "Tokens",
                f"{result.generation_result.input_tokens} → {result.generation_result.output_tokens}",
            )

        st.markdown("---")

        # Final content
        st.subheader("📖 Generated Content")

        tab1, tab2 = st.tabs(["📖 Rendered", "📝 Raw Markdown"])

        with tab1:
            st.markdown(result.final_content)

        with tab2:
            st.code(result.final_content, language="markdown")

        # Download button
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            label="📥 Download Content",
            data=result.final_content,
            file_name=f"generated_content_{timestamp}.md",
            mime="text/markdown",
        )

        st.markdown("---")

        # Analytics
        st.subheader("📊 Token Usage Analytics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Input", f"{result.total_input_tokens:,}")

        with col2:
            st.metric("Total Output", f"{result.total_output_tokens:,}")

        with col3:
            total_tokens = result.total_input_tokens + result.total_output_tokens
            st.metric("Total Tokens", f"{total_tokens:,}")

        with col4:
            # Rough cost estimation for GPT-4o-mini
            estimated_cost = (
                result.total_input_tokens * 0.150 + result.total_output_tokens * 0.600
            ) / 1000000
            st.metric("Est. Cost", f"${estimated_cost:.4f}")

        # Reset button
        if st.button("🔄 Generate New Content", use_container_width=True):
            st.session_state.generation_result = None
            st.session_state.is_generating = False
            st.rerun()


if __name__ == "__main__":
    main()
