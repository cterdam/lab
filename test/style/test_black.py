import subprocess
from pathlib import Path
from test.util import py_files_abs, py_files_rel

import pytest


@pytest.mark.parametrize(
    "file_path",
    py_files_abs,
    ids=[str(pf) for pf in py_files_rel],
)
def test_black(file_path: Path):
    result = subprocess.run(
        ["black", "--check", "--diff", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Bad style - Reformat with Black.")
