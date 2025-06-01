"""
Prompts package for the AI-driven content generation pipeline.

This package contains all prompts organized by component.
"""

from .draft_generation_prompts import (
    DRAFT_GENERATION_PROMPT_TEMPLATE,
    DRAFT_GENERATION_SYSTEM_PROMPT,
)
from .interest_discovery_prompts import (
    INTEREST_DISCOVERY_PROMPT_TEMPLATE,
    INTEREST_DISCOVERY_SYSTEM_PROMPT,
)
from .structural_planning_prompts import (
    STRUCTURAL_PLANNING_PROMPT_TEMPLATE,
    STRUCTURAL_PLANNING_SYSTEM_PROMPT,
)

__all__ = [
    "INTEREST_DISCOVERY_SYSTEM_PROMPT",
    "INTEREST_DISCOVERY_PROMPT_TEMPLATE",
    "STRUCTURAL_PLANNING_SYSTEM_PROMPT",
    "STRUCTURAL_PLANNING_PROMPT_TEMPLATE",
    "DRAFT_GENERATION_SYSTEM_PROMPT",
    "DRAFT_GENERATION_PROMPT_TEMPLATE",
]
