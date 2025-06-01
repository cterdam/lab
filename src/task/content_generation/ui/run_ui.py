#!/usr/bin/env python3
"""
Launcher script for the AI Content Generation Studio UI.

This script starts the Streamlit web interface for the content generation pipeline.
Run this from the project root directory: python src/task/content_generation/ui/run_ui.py
"""

import os
import pathlib
import subprocess
import sys


def main():
    """Launch the Streamlit UI."""

    # Determine if we're running from project root or UI directory
    current_dir = pathlib.Path.cwd()
    ui_file = "src/task/content_generation/ui/content_generation_ui.py"

    # Check if we need to navigate to project root
    if current_dir.name == "ui":
        # Running from UI directory, need to go to project root
        project_root = current_dir.parent.parent.parent.parent
        os.chdir(project_root)
        print(f"📁 Changed to project root: {project_root}")
    elif not pathlib.Path(ui_file).exists():
        print("❌ Error: Please run this script from the project root directory!")
        print("Usage: python src/task/content_generation/ui/run_ui.py")
        sys.exit(1)

    # Check if UI dependencies are installed
    try:
        import streamlit
    except ImportError:
        print("❌ Error: UI dependencies not installed!")
        print("Please install UI dependencies:")
        print("pip install -r src/task/content_generation/ui/requirements-ui.txt")
        print()
        print("Or install all dependencies:")
        print("pip install -r requirements.txt")
        print("pip install -r src/task/content_generation/ui/requirements-ui.txt")
        sys.exit(1)

    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        print()
        print("💡 The UI will run in demo mode without the API key.")
        print()

    print("🚀 Starting AI Content Generation Studio...")
    print("📖 Open your browser and navigate to the URL shown below")
    print()

    try:
        # Launch Streamlit with the UI file
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                ui_file,
                "--server.port",
                "8501",
                "--server.address",
                "localhost",
                "--server.headless",
                "false",
                "--browser.gatherUsageStats",
                "false",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down AI Content Generation Studio...")
    except FileNotFoundError:
        print("❌ Error: Streamlit not found!")
        print("Please install UI dependencies:")
        print("pip install -r src/task/content_generation/ui/requirements-ui.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
