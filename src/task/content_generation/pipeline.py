"""
Content Generation Pipeline for AI-driven content generation.

This module provides a complete pipeline that orchestrates all three components:
1. Interest Discovery
2. Structural Planning
3. Draft Generation
"""

import asyncio
from typing import Optional

from pydantic import Field

from src import log
from src.core import DataCore
from src.lib.model.txt import LmBasis

from .draft_generation import (
    DraftGeneration,
    DraftGenerationParams,
    DraftGenerationResult,
)
from .interest_discovery import (
    InterestDiscovery,
    InterestDiscoveryParams,
    InterestDiscoveryResult,
)
from .structural_planning import (
    StructuralPlanning,
    StructuralPlanningParams,
    StructuralPlanningResult,
)


class ContentGenerationPipelineParams(DataCore):
    """Parameters for the complete content generation pipeline."""

    field_of_topic: str = Field(
        description="The specific field or domain for content generation"
    )

    keywords: str = Field(
        description="Keywords or sentence related to the field of topic"
    )

    content_objectives: str = Field(
        default="Create informative and engaging content that educates the target audience",
        description="Specific objectives for the content to be created",
    )

    target_audience: str = Field(
        default="General audience with interest in the topic",
        description="Description of the target audience for the content",
    )

    content_type: str = Field(
        default="Article/Blog Post",
        description="Type of content to be created (e.g., article, blog post, guide, etc.)",
    )

    additional_instructions: str = Field(
        default="Generate high-quality, engaging content that follows best practices for readability and engagement.",
        description="Additional specific instructions for content generation",
    )

    # Component-specific parameters
    discovery_max_tokens: Optional[int] = Field(
        default=4000, description="Maximum tokens for interest discovery"
    )

    discovery_temperature: float = Field(
        default=0.7, description="Temperature for interest discovery"
    )

    planning_max_tokens: Optional[int] = Field(
        default=3000, description="Maximum tokens for structural planning"
    )

    planning_temperature: float = Field(
        default=0.4, description="Temperature for structural planning"
    )

    generation_max_tokens: Optional[int] = Field(
        default=5000, description="Maximum tokens for draft generation"
    )

    generation_temperature: float = Field(
        default=0.6, description="Temperature for draft generation"
    )


class ContentGenerationPipelineResult(DataCore):
    """Result from the complete content generation pipeline."""

    field_of_topic: str = Field(description="The original field of topic")

    keywords: str = Field(description="The original keywords")

    content_objectives: str = Field(description="The content objectives specified")

    target_audience: str = Field(description="The target audience specified")

    content_type: str = Field(description="The type of content specified")

    # Component results
    discovery_result: InterestDiscoveryResult = Field(
        description="Result from interest discovery component"
    )

    planning_result: StructuralPlanningResult = Field(
        description="Result from structural planning component"
    )

    generation_result: DraftGenerationResult = Field(
        description="Result from draft generation component"
    )

    # Final content
    final_content: str = Field(description="The final generated content")

    # Total token usage
    total_input_tokens: int = Field(
        description="Total input tokens used across all components"
    )

    total_output_tokens: int = Field(
        description="Total output tokens generated across all components"
    )


class ContentGenerationPipeline:
    """
    Complete Content Generation Pipeline.

    Orchestrates the three-component pipeline for AI-driven content generation:
    1. Interest Discovery - Discover eye-catching questions based on keywords and field
    2. Structural Planning - Create content structure and strategy
    3. Draft Generation - Generate the final content draft
    """

    def __init__(self, model: LmBasis, log_name: str = "content_generation_pipeline"):
        """
        Initialize the content generation pipeline.

        Args:
            model: Language model to use for all components
            log_name: Name for logging purposes
        """
        self.model = model
        self.logger = log.bind(component=log_name)

        # Initialize all components
        self.discovery = InterestDiscovery(model, "interest_discovery")
        self.planning = StructuralPlanning(model, "structural_planning")
        self.generation = DraftGeneration(model, "draft_generation")

    def generate_content(
        self, params: ContentGenerationPipelineParams
    ) -> ContentGenerationPipelineResult:
        """
        Generate content using the complete pipeline synchronously.

        Args:
            params: Parameters for the pipeline

        Returns:
            ContentGenerationPipelineResult containing all results and final content
        """
        self.logger.info(
            f"Starting content generation pipeline for field: {params.field_of_topic}, keywords: {params.keywords}"
        )

        # Step 1: Interest Discovery
        self.logger.info("Step 1: Interest Discovery")
        discovery_params = InterestDiscoveryParams(
            field_of_topic=params.field_of_topic,
            keywords=params.keywords,
            max_tokens=params.discovery_max_tokens,
            temperature=params.discovery_temperature,
        )
        discovery_result = self.discovery.discover(discovery_params)

        # Step 2: Structural Planning
        self.logger.info("Step 2: Structural Planning")
        planning_params = StructuralPlanningParams(
            background_research=discovery_result.interest_analysis,
            content_objectives=params.content_objectives,
            target_audience=params.target_audience,
            content_type=params.content_type,
            max_tokens=params.planning_max_tokens,
            temperature=params.planning_temperature,
        )
        planning_result = self.planning.plan(planning_params)

        # Step 3: Draft Generation
        self.logger.info("Step 3: Draft Generation")
        generation_params = DraftGenerationParams(
            background_research=discovery_result.interest_analysis,
            structural_plan=planning_result.structural_plan,
            additional_instructions=params.additional_instructions,
            max_tokens=params.generation_max_tokens,
            temperature=params.generation_temperature,
        )
        generation_result = self.generation.generate(generation_params)

        # Calculate total token usage
        total_input_tokens = (
            discovery_result.input_tokens
            + planning_result.input_tokens
            + generation_result.input_tokens
        )
        total_output_tokens = (
            discovery_result.output_tokens
            + planning_result.output_tokens
            + generation_result.output_tokens
        )

        # Create final result
        result = ContentGenerationPipelineResult(
            field_of_topic=params.field_of_topic,
            keywords=params.keywords,
            content_objectives=params.content_objectives,
            target_audience=params.target_audience,
            content_type=params.content_type,
            discovery_result=discovery_result,
            planning_result=planning_result,
            generation_result=generation_result,
            final_content=generation_result.content_draft,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
        )

        self.logger.success("Content generation pipeline completed successfully")
        self.logger.info(
            f"Total tokens used: {total_input_tokens} input, {total_output_tokens} output"
        )

        return result

    async def agenerate_content(
        self, params: ContentGenerationPipelineParams
    ) -> ContentGenerationPipelineResult:
        """
        Generate content using the complete pipeline asynchronously.

        Args:
            params: Parameters for the pipeline

        Returns:
            ContentGenerationPipelineResult containing all results and final content
        """
        self.logger.info(
            f"Starting async content generation pipeline for field: {params.field_of_topic}, keywords: {params.keywords}"
        )

        # Step 1: Interest Discovery
        self.logger.info("Step 1: Interest Discovery")
        discovery_params = InterestDiscoveryParams(
            field_of_topic=params.field_of_topic,
            keywords=params.keywords,
            max_tokens=params.discovery_max_tokens,
            temperature=params.discovery_temperature,
        )
        discovery_result = await self.discovery.adiscover(discovery_params)

        # Step 2: Structural Planning
        self.logger.info("Step 2: Structural Planning")
        planning_params = StructuralPlanningParams(
            background_research=discovery_result.interest_analysis,
            content_objectives=params.content_objectives,
            target_audience=params.target_audience,
            content_type=params.content_type,
            max_tokens=params.planning_max_tokens,
            temperature=params.planning_temperature,
        )
        planning_result = await self.planning.aplan(planning_params)

        # Step 3: Draft Generation
        self.logger.info("Step 3: Draft Generation")
        generation_params = DraftGenerationParams(
            background_research=discovery_result.interest_analysis,
            structural_plan=planning_result.structural_plan,
            additional_instructions=params.additional_instructions,
            max_tokens=params.generation_max_tokens,
            temperature=params.generation_temperature,
        )
        generation_result = await self.generation.agenerate(generation_params)

        # Calculate total token usage
        total_input_tokens = (
            discovery_result.input_tokens
            + planning_result.input_tokens
            + generation_result.input_tokens
        )
        total_output_tokens = (
            discovery_result.output_tokens
            + planning_result.output_tokens
            + generation_result.output_tokens
        )

        # Create final result
        result = ContentGenerationPipelineResult(
            field_of_topic=params.field_of_topic,
            keywords=params.keywords,
            content_objectives=params.content_objectives,
            target_audience=params.target_audience,
            content_type=params.content_type,
            discovery_result=discovery_result,
            planning_result=planning_result,
            generation_result=generation_result,
            final_content=generation_result.content_draft,
            total_input_tokens=total_input_tokens,
            total_output_tokens=total_output_tokens,
        )

        self.logger.success("Async content generation pipeline completed successfully")
        self.logger.info(
            f"Total tokens used: {total_input_tokens} input, {total_output_tokens} output"
        )

        return result
