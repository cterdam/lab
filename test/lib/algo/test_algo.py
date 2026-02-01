from datetime import timedelta

import pytest

from src import log
from src.core.func_result import Timed
from src.lib.algo.algo import Algo, Input, Output


class DummyInput(Input):
    value: int


class DummyOutput(Output):
    result: int


class DummyAlgo(Algo[DummyInput, DummyOutput]):
    @log.input()
    async def _run(self, inp: DummyInput) -> DummyOutput:
        self.info(f"Running DummyAlgo with {inp.value}")
        return DummyOutput(result=inp.value * 2)


@pytest.mark.asyncio(scope="session")
async def test_algo_timing_integration():
    # 1. Test instantiation
    algo = DummyAlgo(logname="test_timed_dummy")

    # 2. Test input
    inp = DummyInput(value=21)

    # 3. Test timed run
    # run() returns Timed[OutputT]
    timed_res = await algo.run(inp)

    # Verify Timed wrapper
    assert isinstance(timed_res, Timed)
    assert isinstance(timed_res.time, timedelta)
    assert timed_res.time.total_seconds() >= 0

    # Verify encapsulated output
    assert isinstance(timed_res.data, DummyOutput)
    assert timed_res.data.result == 42
    assert timed_res.data.sid > inp.sid
