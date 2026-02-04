import pytest

from src.lib.algo.aswan import (
    AswanInput,
    AswanNormal,
    AswanSim,
    AswanSimInput,
)


@pytest.mark.asyncio(scope="session")
async def test_aswan_normal_basic():
    algo = AswanNormal(logname="test_norm")

    inp = AswanInput(N=100, M=10, p=0.95, y=0.8)

    outp = await algo.run(inp)
    assert outp.data.x >= 16


@pytest.mark.asyncio(scope="session")
async def test_aswan_sim_basic():
    algo = AswanSim(logname="test_sim")

    # Smaller population for faster simulation
    inp = AswanSimInput(
        N=50,
        M=5,
        p=0.90,
        y=0.7,
        num_simulations=100,
    )

    outp = await algo.run(inp)
    assert outp.data.x > 0
