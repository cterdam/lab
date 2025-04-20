import subprocess

import pytest

from src.core.util.constants import PYTHON_FILES_ABSOLUTE, PYTHON_FILES_RELATIVE


@pytest.mark.style
@pytest.mark.parametrize(
    "file_path",
    PYTHON_FILES_ABSOLUTE,
    ids=PYTHON_FILES_RELATIVE,
)
def test_isort(file_path):
    result = subprocess.run(
        ["isort", "--check", "--diff", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Bad imports - Sort with isort.")
