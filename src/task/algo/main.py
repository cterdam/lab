import asyncio
import importlib

from src import arg, log


async def _run_algo():

    path, name = arg.algo.rsplit(".", 1)
    mod = importlib.import_module(path)
    cls = getattr(mod, name)
    log.info(f"Algo loaded: {arg.algo}")

    inp = cls.input_type()
    log.info(inp)

    algo = cls(logname="run")
    result = await algo.run(inp)
    log.success(result)


def main():
    asyncio.run(_run_algo())
