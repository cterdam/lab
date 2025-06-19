import importlib.util
from functools import cached_property
from pathlib import Path

import rich.pretty
from pydantic import ConfigDict, Field, computed_field

from src.core import Logger
from src.core.data_core import DataCore
from src.core.util import multiline


class Environment(DataCore):
    """Context info about the run which are not set by the user."""

    # For pydantic to allow non-Pydantic fields
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @computed_field
    @cached_property
    def repo_root(self) -> Path:
        """Root path of the repo.
        This is assumed to be the parent of the `src` folder.
        """
        module_spec = importlib.util.find_spec("src")
        if module_spec is None or module_spec.origin is None:
            raise ModuleNotFoundError("Could not locate src module.")
        src_path = Path(module_spec.origin).parent
        repo_root = src_path.parent
        return repo_root

    @computed_field
    @cached_property
    def py_files_abs(self) -> list[Path]:
        """Absolute paths to all .py files in this repo."""
        return list(self.repo_root.rglob("*.py"))

    @computed_field
    @cached_property
    def py_file_rel(self) -> list[str]:
        """Relative paths to all .py files in this repo, from repo root."""
        return [
            str(py_file.relative_to(self.repo_root)) for py_file in self.py_files_abs
        ]

    @computed_field
    @cached_property
    def run_name(self) -> str:
        """Name of the current run."""
        # Lazy import to avoid circular import problem
        from src import arg

        if arg.run_name:
            return arg.run_name
        else:
            import getpass
            from datetime import datetime, timezone

            import ulid

            username: str = getpass.getuser()[:4]
            timedate: str = datetime.now(timezone.utc).strftime("%y%m%d-%H%M%S")
            randhash: str = ulid.new().str[-4:]
            uniqueid: str = f"{username}-{timedate}-{randhash}"
            return uniqueid

    @computed_field
    @cached_property
    def out_dir(self) -> Path:
        """Dir to hold all outputs of the current run."""
        return self.repo_root / "out" / self.run_name

    @computed_field
    @cached_property
    def log_dir(self) -> Path:
        """Dir to hold all logs of the run."""
        return self.out_dir / "log"

    loggers: dict[str, Logger] = Field(
        default=dict(),
        description=multiline(
            """
            Maps each logger ID to the instance that has the ID.
            """
        ),
    )

    indent: int = Field(
        default=4,
        description=multiline(
            """
            Default indentation for string formatting.
            """
        ),
    )

    max_linelen: int = Field(
        default=80,
        description=multiline(
            """
            Maximum line length for string formatting.
            """
        ),
    )

    def repr(
        self,
        obj,
        *,
        max_width: int | None = None,
        indent: int | None = None,
    ):
        """Format an arbitrary object for str output, using env defaults."""
        return rich.pretty.pretty_repr(
            obj,
            max_width=max_width or self.max_linelen,
            indent_size=indent or self.indent,
            expand_all=True,
        )
