import gc
import weakref
from io import StringIO

import loguru
import pytest

from src.core import Logger


def test_logger_sink_tracking():
    """Verify that add_sink tracks sink IDs in self.sinks."""
    log = Logger(logname="test_tracking")
    assert len(log.sinks) == 1

    sid = log.add_sink(StringIO())
    assert len(log.sinks) == 2
    assert log.sinks[1] == sid

    # Cleanup for this test
    del log
    gc.collect()


def test_logger_automatic_cleanup():
    """Verify that sinks are removed from loguru when Logger is deleted."""
    log = Logger(logname="test_cleanup")
    sink_ids = log.sinks.copy()
    assert len(sink_ids) > 0

    # Ensure sinks are active in loguru
    # We can't easily inspect loguru handlers directly without private API access,
    # but we can verify remove_sink doesn't raise ValueError yet.
    # Actually, we can check if they exist by trying to remove them (and catching error)
    # but that's destructive.

    # Use weakref to ensure object is gone
    weak_log = weakref.ref(log)

    del log
    gc.collect()

    assert (
        weak_log() is None
    ), "Logger instance was not garbage collected (circular reference leak)"

    # Verify sinks were removed from loguru
    # loguru.logger.remove(id) raises ValueError if id is invalid.
    for sid in sink_ids:
        with pytest.raises(ValueError, match="There is no existing handler"):
            loguru.logger.remove(sid)


def test_logger_mro_del_call():
    """Verify that Logger.__del__ maintains the MRO by calling super().__del__."""

    class SuperClass:
        def __init__(self):
            self.super_del_called = False
            # Store in a class var because instance will be deleted
            SuperClass.last_del_called = False

        def __del__(self):
            SuperClass.last_del_called = True

    class SubLogger(Logger, SuperClass):
        def __init__(self, logname):
            SuperClass.__init__(self)
            Logger.__init__(self, logname=logname)

    sl = SubLogger(logname="test_mro")
    del sl
    gc.collect()

    assert SuperClass.last_del_called, "super().__del__ was not called"


def test_logger_weak_self_in_patch():
    """Verify that the patch lambda doesn't leak memory via self reference."""
    # This is indirectly tested by test_logger_automatic_cleanup,
    # but let's be explicit.

    log = Logger(logname="test_leak")
    weak_log = weakref.ref(log)

    # Trigger a log to exercise the patch lambda
    log.info("test")

    del log
    gc.collect()

    assert weak_log() is None, "Circular reference in patch lambda prevented GC"
