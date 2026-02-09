import asyncio
import inspect
import typing

from src import arg, log
from src.core.arguments import Arguments
from src.core.util import REPO_ROOT, descendant_classes
from src.lib.algo.algo import Algo, Input, Output

import src.lib.algo.aswan  # noqa: F401 — register Aswan subclasses

# Auto-generated Dataclass fields to hide from the user.
_AUTO_FIELDS = frozenset({"cls", "sid"})


def _type_name(annotation) -> str:
    """Clean type name for display."""
    return getattr(annotation, "__name__", str(annotation))


def _concrete_algos() -> dict[str, type[Algo]]:
    """Return name -> class for all concrete (non-abstract) Algo subclasses."""
    return dict(
        sorted(
            (
                (name, cls)
                for name, cls in descendant_classes(Algo).items()
                if not inspect.isabstract(cls)
            ),
            key=lambda pair: pair[0],
        )
    )


def _input_output_types(algo_cls: type[Algo]) -> tuple[type[Input], type[Output]]:
    """Derive (InputType, OutputType) from the algo's _run signature."""
    hints = typing.get_type_hints(algo_cls._run)
    return hints["inp"], hints["return"]


def _user_fields(model_cls: type) -> dict:
    """Fields the user should provide (skip auto-generated ones)."""
    return {
        name: field
        for name, field in model_cls.model_fields.items()
        if name not in _AUTO_FIELDS
    }


def _read_algo_params() -> dict[str, str]:
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


def _print_list() -> None:
    """Print available algos with input / output schemas."""
    algos = _concrete_algos()
    log.info("Available algos:")
    for name, cls in algos.items():
        inp_type, out_type = _input_output_types(cls)
        inp_fields = _user_fields(inp_type)
        out_fields = _user_fields(out_type)

        log.info(f"\n  {name}")

        log.info(f"    Input ({inp_type.__name__}):")
        for fname, finfo in inp_fields.items():
            tname = _type_name(finfo.annotation)
            req = "required" if finfo.is_required() else f"default={finfo.default}"
            desc = finfo.description or ""
            log.info(f"      {fname:<20s} {tname:<8s} ({req})  {desc}")

        log.info(f"    Output ({out_type.__name__}):")
        for fname, finfo in out_fields.items():
            tname = _type_name(finfo.annotation)
            desc = finfo.description or ""
            log.info(f"      {fname:<20s} {tname:<8s} {desc}")


async def _run_algo():
    algos = _concrete_algos()

    if not arg.algo:
        _print_list()
        return

    algo_name = arg.algo
    if algo_name not in algos:
        log.error(f"Unknown algo '{algo_name}'. Available: {', '.join(algos)}")
        return

    algo_cls = algos[algo_name]
    inp_type, _ = _input_output_types(algo_cls)
    params = _read_algo_params()

    log.info(f"Algo:   {algo_name}")
    log.info(f"Params: {params}")

    inp = inp_type(**params)

    algo = algo_cls(logname=f"launch_{algo_name}")
    result = await algo.run(inp)

    for name in _user_fields(type(result.data)):
        log.success(f"{name}={getattr(result.data, name)}")


def main():
    asyncio.run(_run_algo())
