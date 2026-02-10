import asyncio
import importlib
import typing

from src import arg, log
from src.core.arguments import Arguments
from src.core.util import REPO_ROOT, multiline

# Auto-generated Dataclass fields to hide from the user.
_AUTO_FIELDS = frozenset({"cls", "sid"})


def _fields(cls: type) -> dict:
    """Fields the user should provide (skip auto-generated ones)."""
    return {
        name: field
        for name, field in cls.model_fields.items()
        if name not in _AUTO_FIELDS
    }


def _read_params() -> dict[str, str]:
    """Read algo params from the args file.

    Any key=value pair whose key is not a known Arguments field is treated as
    an algo parameter.  This lets every algo receive its canonical params
    straight from the args file without polluting Arguments.
    """
    known = set(Arguments.model_fields.keys())
    params: dict[str, str] = {}
    with open(REPO_ROOT / "args") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key not in known:
                params[key] = value
    return params


async def _run():
    path, name = arg.algo.rsplit(".", 1)
    mod = importlib.import_module(path)
    cls = getattr(mod, name)

    hints = typing.get_type_hints(cls._run)
    inp_t = hints["inp"]

    params = _read_params()

    log.info(
        multiline(
            f"""
        Algo:   {arg.algo}
        Params: {params}
        """,
            oneline=False,
        )
    )

    inp = inp_t(**params)

    algo = cls(logname=f"launch_{name}")
    result = await algo.run(inp)

    msg = "\n".join(
        f"{fname}={getattr(result.data, fname)}" for fname in _fields(type(result.data))
    )
    log.success(msg)


def main():
    asyncio.run(_run())
