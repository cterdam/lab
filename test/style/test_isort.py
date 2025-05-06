import subprocess

import pytest

from src import env


@pytest.mark.style
@pytest.mark.parametrize(
    "file_path",
    env.py_files_abs,
    ids=env.py_file_rel,
)
def test_isort(file_path):
    result = subprocess.run(
        ["isort", "--check", "--diff", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Bad imports - Sort with isort.")
