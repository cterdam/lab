# AI Content Generation Studio UI

A beautiful, modern web interface for the AI Content Generation Pipeline. This UI provides an intuitive way to interact with the three-agent content generation system.

## Features

🎯 **Multi-Agent System**
- **Discovery Agent**: Finds engaging questions and content angles
- **Planning Agent**: Creates structured content plans  
- **Writer Agent**: Generates final polished content

🎨 **Beautiful Interface**
- Modern gradient design with responsive layout
- Real-time progress tracking with visual feedback
- Interactive agent status cards
- Professional markdown rendering

📊 **Advanced Analytics**
- Token usage tracking across all agents
- Cost estimation for GPT-4o-mini
- Interactive charts and visualizations
- Performance metrics dashboard

⚙️ **Comprehensive Configuration**
- Customizable creativity levels per agent
- Token limit controls
- Content type and audience targeting
- Advanced prompt engineering options

💾 **Export & Sharing**
- Download generated content with timestamps
- Raw and rendered markdown views
- Structured output format

## Installation

### 1. Install UI Dependencies

From the project root directory:

```bash
# Install UI-specific dependencies
pip install -r src/task/content_generation/ui/requirements-ui.txt

# Or install all project dependencies first, then UI dependencies
pip install -r requirements.txt
pip install -r src/task/content_generation/ui/requirements-ui.txt
```

### 2. Set OpenAI API Key

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-api-key-here"

# Windows Command Prompt  
set OPENAI_API_KEY=your-api-key-here

# Linux/Mac
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Quick Start

From the **project root directory**:

```bash
python src/task/content_generation/ui/run_ui.py
```

### Alternative Launch Methods

```bash
# Direct streamlit command
streamlit run src/task/content_generation/ui/content_generation_ui.py

# From UI directory (script will auto-navigate to project root)
cd src/task/content_generation/ui
python run_ui.py
```

### Demo Mode

The UI includes a demo mode that works even without API keys or full dependencies:
- Shows sample content generation results
- Demonstrates all UI features
- Useful for testing and development

## Directory Structure

```
src/task/content_generation/ui/
├── content_generation_ui.py    # Main Streamlit application
├── run_ui.py                   # Launcher script
├── requirements-ui.txt         # UI-specific dependencies
├── README.md                   # This documentation
└── __init__.py                 # Python package initialization
```

## Configuration Options

### Basic Settings
- **Field of Topic**: The domain/subject area
- **Keywords**: Key terms to focus content around
- **Content Objectives**: What the content should achieve
- **Target Audience**: Who the content is for
- **Content Type**: Blog post, article, guide, etc.

### Advanced Settings
- **Token Limits**: Control output length per agent
- **Creativity Levels**: Adjust temperature settings
- **Custom Instructions**: Additional guidance for agents

## Troubleshooting

### Common Issues

**Import Errors**: 
- Ensure you're running from the project root directory
- Install all dependencies: `pip install -r requirements.txt`
- Install UI dependencies: `pip install -r src/task/content_generation/ui/requirements-ui.txt`

**API Key Issues**:
- Set the OPENAI_API_KEY environment variable
- The UI will run in demo mode without a valid API key

**Port Conflicts**:
- Streamlit will automatically find an available port
- Default is localhost:8501

**Module Not Found**:
- Make sure you're running from the project root, not the UI subdirectory
- Check that all Python paths are correctly configured

### Getting Help

1. Check the error messages in the UI - they provide specific guidance
2. Try the demo mode first to test the interface
3. Verify the basic pipeline works: `python -m src.task.content_generation.test_pipeline`
4. Check logs in the `out/` directory for detailed error information

## Development

### Isolated Dependencies

The UI dependencies are isolated in `requirements-ui.txt` to avoid conflicts with the core project:

- **Core Project**: Uses `requirements.txt` for AI/ML dependencies
- **UI Module**: Uses `requirements-ui.txt` for web interface dependencies

This allows the core content generation pipeline to remain lightweight while adding rich UI capabilities as an optional component.

### Architecture

The UI is built with:
- **Streamlit**: Web framework and reactive UI
- **Plotly**: Interactive charts and visualizations  
- **Pandas**: Data processing for analytics
- **python-dotenv**: Environment variable management

The interface communicates with the content generation pipeline through well-defined Python APIs, making it easy to extend or modify either component independently. 