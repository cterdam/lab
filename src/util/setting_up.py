"""Utilities that cannot be included in src.util because of dependency issues.

Typically, these are utilities involved in the setting up of a run.
"""

import os
import random
from typing import Callable

from src.log import logger

__all__ = [
    "get_random_state_setter",
]


def get_random_state_setter(config) -> Callable[[], None]:
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

        # Logging msgs for setting random state
        logger.debug("Setting up random state.")

        if config.random.python_seed is not None:
            random.seed(config.random.python_seed)
            logger.debug(f"Python random seed set to {config.random.python_seed}.")
        else:
            logger.debug("NOT setting Python random seed.")

        if config.random.numpy_seed is not None:
            np.random.seed(config.random.numpy_seed)
            logger.debug(f"Numpy random seed set to {config.random.numpy_seed}.")
        else:
            logger.debug("NOT setting Numpy random seed.")

        if config.random.torch_seed is not None:
            torch.manual_seed(config.random.torch_seed)
            logger.debug(f"Torch manual seed set to {config.random.torch_seed}.")
        else:
            logger.debug("NOT setting torch manual seed.")

        if config.random.torch_backends_cudnn_benchmark is not None:
            torch.backends.cudnn.benchmark = (
                config.random.torch_backends_cudnn_benchmark
            )
            logger.debug(
                multiline(
                    f"""
                    Torch backends cudnn benchmark set to
                    {config.random.torch_backends_cudnn_benchmark}.
                    """
                )
            )
        else:
            logger.debug("NOT setting torch backends cudnn benchmark.")

        if config.random.torch_use_deterministic_algorithms is not None:
            torch.use_deterministic_algorithms(
                config.random.torch_use_deterministic_algorithms
            )
            logger.debug(
                multiline(
                    f"""
                    Torch deterministic algorithms use set to
                    {config.random.torch_use_deterministic_algorithms}.
                    """
                )
            )
        else:
            logger.debug("NOT setting torch use deterministic algorithms.")

        if config.random.cublas_workspace_config is not None:
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = (
                config.random.cublas_workspace_config
            )
            logger.debug(
                multiline(
                    f"""
                    Cublas workspace config set to
                    {config.random.cublas_workspace_config}
                    """
                )
            )
        else:
            logger.debug("NOT setting cublas workspace config.")

        logger.debug("Finished setting up random state.")

    return random_state_setter
