from src.core.util import get_project_root

PROJECT_ROOT = get_project_root()
PYTHON_FILES_ABSOLUTE = list(PROJECT_ROOT.rglob("*.py"))
PYTHON_FILES_RELATIVE = [
    str(python_file.relative_to(PROJECT_ROOT)) for python_file in PYTHON_FILES_ABSOLUTE
]
