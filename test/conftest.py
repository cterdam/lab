import importlib.util
from pathlib import Path

import pytest


def _get_repo_root() -> Path:
    """Helper function to find the repo root."""
    module_spec = importlib.util.find_spec("src")
    if module_spec is None or module_spec.origin is None:
        raise ModuleNotFoundError("Could not locate src module.")
    src_path = Path(module_spec.origin).parent
    return src_path.parent


def pytest_generate_tests(metafunc):
    if "file_path" in metafunc.fixturenames:
        repo_root = _get_repo_root()
        all_py_files = list(repo_root.rglob("*.py"))
        all_py_files_rel = [
            str(py_file.relative_to(repo_root)) for py_file in all_py_files
        ]
        metafunc.parametrize(
            "file_path",
            all_py_files,
            ids=all_py_files_rel,
        )
