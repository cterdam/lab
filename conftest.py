import os
import sys

# pydantic_settings with cli_parse_args=True reads sys.argv, which
# conflicts with pytest's own args. Strip everything after the script
# name so the Arguments model sees no CLI flags.
sys.argv = sys.argv[:1]

# Ensure required env vars are set for tests.
os.environ.setdefault("RUN_ID", "test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("REDIS_INSIGHT", "localhost:8001")
