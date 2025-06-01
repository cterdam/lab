#!/usr/bin/env python3
"""
Convenience launcher for the AI Content Generation Studio UI.

Run this from the project root or from the content_generation directory.
This script calls the UI launcher from its organized location.
"""

import os
import pathlib
import subprocess
import sys


def main():
    """Launch the UI with proper path handling."""

    current_dir = pathlib.Path.cwd()

    # Determine the correct path to the UI launcher
    if current_dir.name == "content_generation":
        # Running from content_generation directory
        ui_launcher = "ui/run_ui.py"
        # Change to project root for proper module imports
        project_root = current_dir.parent.parent
        os.chdir(project_root)
        ui_launcher = "src/task/content_generation/ui/run_ui.py"
    elif current_dir.name == "asktheworld" or (current_dir / "src").exists():
        # Running from project root
        ui_launcher = "src/task/content_generation/ui/run_ui.py"
    else:
        print(
            "❌ Error: Please run this from the project root or content_generation directory"
        )
        print("Usage:")
        print("  From project root: python src/task/content_generation/launch_ui.py")
        print("  From content_generation: python launch_ui.py")
        sys.exit(1)

    try:
        subprocess.run([sys.executable, ui_launcher], check=True)
    except Exception as e:
        print(f"❌ Error launching UI: {e}")
        print("Try running directly: python src/task/content_generation/ui/run_ui.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
