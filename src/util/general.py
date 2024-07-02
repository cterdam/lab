from datetime import datetime, timezone
import getpass
import os
import random
import textwrap
from types import NoneType, UnionType
from typing import Any, Callable, Literal, Type, Union, _UnionGenericAlias, get_args

import ulid
from yaml import safe_load


__all__ = [
    "get_unique_id",
    "multiline",
    "load_yaml_file",
    "load_yaml_var",
    "get_type_name",
    "denonify",
    "get_random_state_setter",
    "get_non_special_regex",
]


def get_unique_id() -> str:
    """Prepare a unique identifier for a run."""
    _username: str = getpass.getuser()[:4]
    _datetime: str = datetime.now(timezone.utc).strftime("%m%d-%H%M")
    _randhash: str = ulid.new().str[-4:]
    unique_id: str = f"{_username}-{_datetime}-{_randhash}"
    return unique_id


def multiline(s: str, is_url: bool = False) -> str:
    """Correctly connect a multiline string.

    Args:
        s (str): A string, usually formed with three double quotes.

    Returns:
        str: A string formed by removing all common whitespaces near the start of each
        line in the original string.
    """
    result = textwrap.dedent(s).replace("\n", " ").strip()
    if is_url:
        result = result.replace(" ", "")
    return result


def load_yaml_file(filepath) -> dict:
    with open(filepath) as f:
        result = safe_load(f)
    return result


def load_yaml_var(v: str) -> Any:
    """Given a string, interpret it as a variable using yaml's load logic."""
    return safe_load(f"key: {v}")["key"]


def get_type_name(t: Type | UnionType) -> str:
    """Given a type, infer the class name in str."""
    if hasattr(t, "__origin__") and t.__origin__ is Literal:
        # Literal type
        return "Literal[" + ", ".join(repr(arg) for arg in get_args(t)) + "]"
    if isinstance(t, UnionType) or isinstance(t, _UnionGenericAlias):
        # UnionType -> int | None
        # _UnionGenericAlias -> typing.Optional[int]
        return str(t)
    else:
        return t.__name__


def denonify(ut: UnionType) -> NoneType | Type | UnionType:
    """Given a union type, return the non-None base type(s) in it."""
    union_args = get_args(ut)
    non_none_types = [arg for arg in union_args if arg is not NoneType]
    match non_none_types:
        case []:
            return None
        case [t]:
            return t
        case _:
            return Union[tuple(non_none_types)]


def get_random_state_setter(config, logger) -> Callable[[], None]:
    """Given the lab config, return a function that sets the random state.

    Arguments:
        config (LabConfig)

    Returns (Callable[[], None]):
        A function that sets the various random state according to the config.
    """

    ###################################################################################
    # Lazy import on time-consuming imports
    torch_args = (
        config.random.torch_seed,
        config.random.torch_backends_cudnn_benchmark,
        config.random.torch_use_deterministic_algorithms,
    )
    if any([optval is not None for optval in torch_args]):
        import torch
    if config.random.numpy_seed is not None:
        import numpy as np
    ###################################################################################

    def random_state_setter():

        logger.trace("Setting up random state.")

        if config.random.python_seed is not None:
            random.seed(config.random.python_seed)
            logger.trace(f"Python random seed set to {config.random.python_seed}.")
        else:
            logger.trace("NOT setting Python random seed.")

        if config.random.numpy_seed is not None:
            np.random.seed(config.random.numpy_seed)
            logger.trace(f"Numpy random seed set to {config.random.numpy_seed}.")
        else:
            logger.trace("NOT setting Numpy random seed.")

        if config.random.torch_seed is not None:
            torch.manual_seed(config.random.torch_seed)
            logger.trace(f"Torch manual seed set to {config.random.torch_seed}.")
        else:
            logger.trace("NOT setting torch manual seed.")

        if config.random.torch_backends_cudnn_benchmark is not None:
            torch.backends.cudnn.benchmark = (
                config.random.torch_backends_cudnn_benchmark
            )
            logger.trace(
                multiline(
                    f"""
                    Torch backends cudnn benchmark set to
                    {config.random.torch_backends_cudnn_benchmark}.
                    """
                )
            )
        else:
            logger.trace("NOT setting torch backends cudnn benchmark.")

        if config.random.torch_use_deterministic_algorithms is not None:
            torch.use_deterministic_algorithms(
                config.random.torch_use_deterministic_algorithms
            )
            logger.trace(
                multiline(
                    f"""
                    Torch deterministic algorithms use set to
                    {config.random.torch_use_deterministic_algorithms}.
                    """
                )
            )
        else:
            logger.trace("NOT setting torch use deterministic algorithms.")

        if config.random.cublas_workspace_config is not None:
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = (
                config.random.cublas_workspace_config
            )
            logger.trace(
                multiline(
                    f"""
                    Cublas workspace config set to
                    {config.random.cublas_workspace_config}
                    """
                )
            )
        else:
            logger.trace("NOT setting cublas workspace config.")

    return random_state_setter


def get_non_special_regex() -> str:
    """
    Returns a regex pattern that matches any string with at least 1 char which does not
    include any special chars.
    """
    pattern = r'^[^ `~!@#$%^&*()\[\]{}\\|;:\'",<.>/?]+$'
    return pattern
