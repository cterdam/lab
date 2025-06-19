import re

import pytest

from src.core.util import as_filename, randalnu


def test_as_filename_basic():
    assert as_filename("openai/gpt-4.1") == "openai_gpt-4_1"


def test_as_filename_emojis_symbols():
    assert (
        as_filename("mistral‑ai/mixtral‑8x7b‑inst/💡") == "mistral_ai_mixtral_8x7b_inst"
    )


def test_as_filename_strips_extra_underscores():
    assert as_filename("///hello///") == "hello"


def test_as_filename_consecutive_special_chars():
    assert as_filename("hello!!world") == "hello_world"


def test_as_filename_invalid():
    with pytest.raises(ValueError):
        as_filename("💡💡💡")


def test_randalnu_default_length():
    result = randalnu()
    assert isinstance(result, str)
    assert len(result) == 4
    assert re.match(r"^[a-z0-9]{4}$", result)


def test_randalnu_custom_length():
    for length in [1, 6, 10]:
        result = randalnu(length)
        assert len(result) == length
        assert re.match(r"^[a-z0-9]+$", result)


def test_randalnu_randomness():
    num_trials = 100
    samples = {randalnu() for _ in range(num_trials)}
    assert len(samples) == num_trials
