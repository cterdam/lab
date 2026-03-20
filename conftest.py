import os

# Ensure env vars are set before src imports
os.environ.setdefault("RUN_ID", "test")
os.environ.setdefault("REDIS_INSIGHT", "")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
