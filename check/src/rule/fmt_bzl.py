"""Rule: Starlark / BUILD formatting via buildifier.

buildifier is a prebuilt binary (no pip/Node dep); the package passes it in via
files = {"buildifier": "@buildifier_prebuilt//:buildifier"}.
"""

import os
import subprocess
from pathlib import Path


def rule(path: Path, buildifier) -> None:
    proc = subprocess.run(
        [os.path.abspath(buildifier), "-mode=check", "-lint=off", str(path)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        out = (proc.stdout + proc.stderr).strip()
        raise AssertionError(
            f"buildifier: not formatted (run: buildifier {path})\n{out}"
        )
