import getpass
import importlib.util
import pathlib
from datetime import datetime, timezone
from functools import cached_property

import ulid
from pydantic import Field, computed_field

from src.core.data_core import DataCore
from src.core.util import multiline


class Environment(DataCore):
    """Context info about the run which are not set by the user."""

    @computed_field
    @cached_property
    def repo_root(self) -> pathlib.Path:
        """Return the root path of the repo.
        This is assumed to be the parent of the `src` folder.
        """
        module_spec = importlib.util.find_spec("src")
        if module_spec is None or module_spec.origin is None:
            raise ModuleNotFoundError("Could not locate src module.")
        src_path = pathlib.Path(module_spec.origin).parent
        repo_root = src_path.parent
        return repo_root

    @computed_field
    @cached_property
    def py_files_abs(self) -> list[pathlib.Path]:
        """Return the absolute path to all .py files in this repo."""
        return list(self.repo_root.rglob("*.py"))

    @computed_field
    @cached_property
    def py_file_rel(self) -> list[str]:
        """Return paths to all .py files in this repo, relative to repo root."""
        return [
            str(py_file.relative_to(self.repo_root)) for py_file in self.py_files_abs
        ]

    @computed_field
    @cached_property
    def run_name(self) -> str:
        from src import arg

        if arg.run_name:
            return arg.run_name
        else:
            username: str = getpass.getuser()[:4]
            timedate: str = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
            randhash: str = ulid.new().str[-4:]
            uniqueid: str = f"{username}-{timedate}-{randhash}"
            return uniqueid

    @computed_field
    @cached_property
    def out_dir(self) -> pathlib.Path:
        return self.repo_root / "out" / self.run_name

    indent: int = Field(
        default=4,
        description=multiline(
            """
            Default indentation for string formatting.
            """
        ),
    )
