# AI-Driven Content Generation Pipeline

This project implements a comprehensive AI-driven content generation pipeline with three chained components that work together to create high-quality content from a simple topic input.

## Overview

The pipeline consists of three sequential components:

1. **Background Discovery** - Conducts comprehensive research and analysis of the given topic
2. **Structural Planning** - Creates a detailed content structure and strategy based on the research
3. **Draft Generation** - Generates the final content draft following the structural plan

Each component consumes the output from its upstream component and uses configurable LLM models to complete its specific task.

## Project Structure

```
src/task/content_generation/
├── __init__.py                 # Module initialization
├── README.md                   # This documentation
├── launch_ui.py                # Convenience launcher for web UI
├── prompts.py                  # All LLM prompts for the three components
├── background_discovery.py     # Component 1: Background research and analysis
├── structural_planning.py      # Component 2: Content structure and strategy
├── draft_generation.py         # Component 3: Final content generation
├── pipeline.py                 # Complete pipeline orchestration
├── main.py                     # Entry point and demo examples
└── ui/                         # Web interface components
    ├── content_generation_ui.py    # Streamlit web application
    ├── run_ui.py                   # UI launcher script
    ├── requirements-ui.txt         # UI-specific dependencies
    ├── README.md                   # UI documentation
    └── __init__.py                 # UI module initialization
```

## Components

### 1. Background Discovery (`background_discovery.py`)

**Purpose**: Conducts comprehensive research and background analysis for a given topic.

**Input**: 
- Topic string
- Configuration parameters (max tokens, temperature)

**Output**: 
- Comprehensive background research including:
  - Core concepts and definitions
  - Historical context
  - Current state and trends
  - Key stakeholders and perspectives
  - Related topics and connections
  - Reliable sources and references

**Key Classes**:
- `BackgroundDiscovery`: Main component class
- `BackgroundDiscoveryParams`: Input parameters
- `BackgroundDiscoveryResult`: Output result

### 2. Structural Planning (`structural_planning.py`)

**Purpose**: Transforms background research into a well-organized content structure and strategy.

**Input**: 
- Background research from discovery component
- Content objectives
- Target audience
- Content type
- Configuration parameters

**Output**: 
- Detailed structural plan including:
  - Content strategy overview
  - Hierarchical outline with sections and subsections
  - Content elements and supporting materials
  - Engagement strategy
  - Content guidelines

**Key Classes**:
- `StructuralPlanning`: Main component class
- `StructuralPlanningParams`: Input parameters
- `StructuralPlanningResult`: Output result

### 3. Draft Generation (`draft_generation.py`)

**Purpose**: Generates the final content draft based on the structural plan and background research.

**Input**: 
- Background research
- Structural plan
- Additional instructions
- Configuration parameters

**Output**: 
- Complete, publication-ready content draft that:
  - Follows the provided structure
  - Incorporates research naturally
  - Engages the target audience
  - Achieves stated objectives
  - Meets quality standards

**Key Classes**:
- `DraftGeneration`: Main component class
- `DraftGenerationParams`: Input parameters
- `DraftGenerationResult`: Output result

### 4. Pipeline Orchestration (`pipeline.py`)

**Purpose**: Orchestrates all three components into a seamless pipeline.

**Features**:
- Complete pipeline execution (sync and async)
- Token usage tracking across all components
- Configurable parameters for each component
- Comprehensive result aggregation

**Key Classes**:
- `ContentGenerationPipeline`: Main pipeline class
- `ContentGenerationPipelineParams`: Pipeline parameters
- `ContentGenerationPipelineResult`: Complete pipeline result

## Web Interface

The content generation pipeline includes a beautiful web interface built with Streamlit that provides:

🎯 **Interactive Content Generation**
- Easy-to-use forms for topic and configuration input
- Real-time progress tracking during generation
- Beautiful visualization of all three agent outputs

📊 **Advanced Analytics**
- Token usage tracking across all components
- Cost estimation for different models
- Interactive charts and performance metrics

🎨 **Modern Design**
- Responsive layout with gradient styling
- Agent status cards with visual feedback
- Professional markdown rendering with tabs

### Quick Start with Web UI

```bash
# Install UI dependencies
pip install -r src/task/content_generation/ui/requirements-ui.txt

# Launch the web interface
python src/task/content_generation/launch_ui.py
```

See `ui/README.md` for complete UI documentation and advanced usage.

## Usage

### Running the Complete Pipeline

```python
from src.lib.model.txt.api.openai import OpenaiLm, OpenaiLmInitParams
from src.task.content_generation.pipeline import (
    ContentGenerationPipeline,
    ContentGenerationPipelineParams
)

# Initialize LLM model (configurable)
model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))

# Create pipeline
pipeline = ContentGenerationPipeline(model)

# Configure parameters
params = ContentGenerationPipelineParams(
    topic="Artificial Intelligence in Healthcare",
    content_objectives="Create a comprehensive guide for medical professionals",
    target_audience="Healthcare professionals and administrators",
    content_type="Educational guide",
    additional_instructions="Focus on practical applications and ethical considerations"
)

# Generate content
result = pipeline.generate_content(params)

# Access the final content
print(result.final_content)
```

### Using Individual Components

```python
# Component 1: Background Discovery
discovery = BackgroundDiscovery(model)
discovery_result = discovery.discover(
    BackgroundDiscoveryParams(topic="Your Topic Here")
)

# Component 2: Structural Planning
planning = StructuralPlanning(model)
planning_result = planning.plan_from_discovery(
    discovery_result,
    content_objectives="Your objectives",
    target_audience="Your audience",
    content_type="Your content type"
)

# Component 3: Draft Generation
generation = DraftGeneration(model)
generation_result = generation.generate_from_planning(
    planning_result,
    additional_instructions="Your specific instructions"
)
```

### Async Pipeline for Better Performance

```python
import asyncio

async def generate_multiple_content():
    pipeline = ContentGenerationPipeline(model)
    
    topics = ["Topic 1", "Topic 2", "Topic 3"]
    tasks = []
    
    for topic in topics:
        params = ContentGenerationPipelineParams(topic=topic)
        tasks.append(pipeline.agenerate_content(params))
    
    results = await asyncio.gather(*tasks)
    return results

# Run async pipeline
results = asyncio.run(generate_multiple_content())
```

## Configuration

### LLM Model Configuration

The pipeline supports configurable LLM models. Currently implemented:

- **OpenAI Models**: GPT-4, GPT-4-turbo, GPT-3.5-turbo, etc.
- **Extensible**: Easy to add support for other models (DeepSeek, Claude, etc.)

```python
# OpenAI model
model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))

# Add other models as needed
# model = DeepSeekLm(params=DeepSeekLmInitParams(model_name="deepseek-chat"))
```

### Component Parameters

Each component has configurable parameters:

```python
params = ContentGenerationPipelineParams(
    topic="Your Topic",
    
    # Discovery settings
    discovery_max_tokens=4000,
    discovery_temperature=0.3,  # Lower for more factual content
    
    # Planning settings  
    planning_max_tokens=3000,
    planning_temperature=0.4,   # Balanced
    
    # Generation settings
    generation_max_tokens=5000,
    generation_temperature=0.6  # Higher for more creative content
)
```

## Running the Demo

To run the content generation task:

```bash
python -m src --task content_generation
```

This will run several demos:
1. Individual components demonstration
2. Complete pipeline demonstration
3. Async pipeline demonstration
4. Different models demonstration (when available)

## Prompts

All prompts are stored in `prompts.py` for easy modification and maintenance:

- `BACKGROUND_DISCOVERY_SYSTEM_PROMPT` & `BACKGROUND_DISCOVERY_PROMPT_TEMPLATE`
- `STRUCTURAL_PLANNING_SYSTEM_PROMPT` & `STRUCTURAL_PLANNING_PROMPT_TEMPLATE`  
- `DRAFT_GENERATION_SYSTEM_PROMPT` & `DRAFT_GENERATION_PROMPT_TEMPLATE`

The prompts are designed to be comprehensive and can be customized for specific use cases.

## Token Usage and Cost Management

The pipeline tracks token usage across all components:

```python
result = pipeline.generate_content(params)

print(f"Total input tokens: {result.total_input_tokens}")
print(f"Total output tokens: {result.total_output_tokens}")

# Individual component usage
print(f"Discovery: {result.discovery_result.output_tokens} tokens")
print(f"Planning: {result.planning_result.output_tokens} tokens") 
print(f"Generation: {result.generation_result.output_tokens} tokens")
```

## Error Handling and Logging

The pipeline includes comprehensive logging and error handling:

- Each component logs its progress and results
- Token usage is tracked and reported
- Errors are properly propagated with context
- All operations are logged for debugging and monitoring

## Extending the Pipeline

### Adding New Components

1. Create a new component file following the existing pattern
2. Define parameter and result classes using `DataCore`
3. Implement sync and async methods
4. Add appropriate prompts to `prompts.py`
5. Update the pipeline to include the new component

### Adding New LLM Models

1. Implement the model following the `LmBasis` interface
2. Add model-specific parameter and result classes
3. Update the demo to include the new model
4. Test with the pipeline

## Best Practices

1. **Token Management**: Monitor token usage to control costs
2. **Temperature Settings**: Use lower temperatures for factual content, higher for creative content
3. **Prompt Engineering**: Customize prompts for specific domains or use cases
4. **Async Usage**: Use async methods for better performance when generating multiple pieces of content
5. **Error Handling**: Always handle potential API errors and rate limits
6. **Content Review**: Generated content should be reviewed before publication

## Dependencies

- `pydantic`: For data validation and serialization
- `openai`: For OpenAI API integration
- `python-dotenv`: For environment variable management
- Core project dependencies for logging and utilities

## Environment Setup

Ensure you have the required API keys set up:

```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here
# Add other API keys as needed
``` 