import subprocess
from pathlib import Path

import pytest


# `file_path` is parameterized via the `pytest_generate_tests` hook in conftest.py
def test_isort(file_path: Path):
    result = subprocess.run(
        ["isort", "--check", "--diff", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Bad imports - Sort with isort.")
