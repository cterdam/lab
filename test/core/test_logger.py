import pytest

from src import env
from src.core import Logger


@pytest.fixture(autouse=True)
def reset_logger_state(tmp_path, monkeypatch):
    """Before each test, set the global registry env.out_dir."""
    monkeypatch.setattr(env, "loggers", dict())
    monkeypatch.setattr(env, "out_dir", tmp_path)
    monkeypatch.setattr(env, "repo_root", tmp_path)


def test_duplicate_logger_single_thread():
    dup_name = "dup"
    _ = Logger(logname=dup_name)
    with pytest.raises(ValueError):
        Logger(logname=dup_name)
