"""
Main entry point for the AI-driven content generation task.

This module provides examples of how to use the content generation pipeline
with different LLM models and configurations.
"""

import asyncio

from dotenv import load_dotenv

from src import log
from src.lib.model.txt.api.openai import (
    OpenaiLm,
    OpenaiLmInitParams,
)

from .draft_generation import DraftGeneration, DraftGenerationParams
from .interest_discovery import InterestDiscovery, InterestDiscoveryParams
from .pipeline import ContentGenerationPipeline, ContentGenerationPipelineParams
from .structural_planning import StructuralPlanning, StructuralPlanningParams


def demo_individual_components(model):
    """
    Demonstrate using each component individually with provided model.
    """
    log.info("=== Individual Components Demo ===")

    field_of_topic = "Technology"
    keywords = "artificial intelligence and future of work"

    # Component 1: Interest Discovery
    log.info("Running Interest Discovery...")
    discovery = InterestDiscovery(model)
    discovery_params = InterestDiscoveryParams(
        field_of_topic=field_of_topic, keywords=keywords
    )
    discovery_result = discovery.discover(discovery_params)

    log.info(
        f"Interest analysis generated: {len(discovery_result.interest_analysis)} characters"
    )
    log.info(
        f"Discovery tokens: {discovery_result.input_tokens} input, {discovery_result.output_tokens} output"
    )

    # Component 2: Structural Planning
    log.info("Running Structural Planning...")
    planning = StructuralPlanning(model)
    planning_params = StructuralPlanningParams(
        interest_analysis=discovery_result.interest_analysis,
        content_objectives="Create an engaging article about AI and work for business leaders",
        target_audience="Business executives and decision makers",
        content_type="Professional article",
    )
    planning_result = planning.plan(planning_params)

    log.info(
        f"Structural plan generated: {len(planning_result.structural_plan)} characters"
    )
    log.info(
        f"Planning tokens: {planning_result.input_tokens} input, {planning_result.output_tokens} output"
    )

    # Component 3: Draft Generation
    log.info("Running Draft Generation...")
    generation = DraftGeneration(model)
    generation_params = DraftGenerationParams(
        interest_analysis=discovery_result.interest_analysis,
        structural_plan=planning_result.structural_plan,
        additional_instructions="Focus on practical implications and actionable insights for business leaders.",
    )
    generation_result = generation.generate(generation_params)

    log.info(
        f"Content draft generated: {len(generation_result.content_draft)} characters"
    )
    log.info(
        f"Generation tokens: {generation_result.input_tokens} input, {generation_result.output_tokens} output"
    )

    # Total tokens
    total_input = (
        discovery_result.input_tokens
        + planning_result.input_tokens
        + generation_result.input_tokens
    )
    total_output = (
        discovery_result.output_tokens
        + planning_result.output_tokens
        + generation_result.output_tokens
    )

    log.info(f"Total tokens used: {total_input} input, {total_output} output")


def demo_pipeline(model):
    """
    Demonstrate using the complete pipeline with provided model.
    """
    log.info("=== Complete Pipeline Demo ===")

    pipeline = ContentGenerationPipeline(model)

    params = ContentGenerationPipelineParams(
        field_of_topic="Health & Wellness",
        keywords="intermittent fasting weight loss benefits risks",
        content_objectives="Create an informative yet controversial article about intermittent fasting",
        target_audience="Health-conscious individuals aged 25-45",
        content_type="Blog post",
        additional_instructions="Focus on controversial aspects and recent scientific debates about intermittent fasting.",
    )

    result = pipeline.generate_content(params)

    log.info(f"Pipeline completed for field: {result.field_of_topic}")
    log.info(f"Keywords used: {result.keywords}")
    log.info(f"Final content length: {len(result.final_content)} characters")
    log.info(
        f"Total pipeline tokens: {result.total_input_tokens} input, {result.total_output_tokens} output"
    )

    # Print a preview of each component's output
    log.info("\n--- Interest Discovery Preview ---")
    log.info(result.discovery_result.interest_analysis[:300] + "...")

    log.info("\n--- Structural Plan Preview ---")
    log.info(result.planning_result.structural_plan[:300] + "...")

    log.info("\n--- Final Content Preview ---")
    log.info(result.final_content[:300] + "...")


async def demo_async_pipeline(model):
    """
    Demonstrate using the async pipeline with provided model.
    """
    log.info("=== Async Pipeline Demo ===")

    pipeline = ContentGenerationPipeline(model)

    params = ContentGenerationPipelineParams(
        field_of_topic="Finance",
        keywords="cryptocurrency bitcoin regulation government control",
        content_objectives="Create a provocative article about cryptocurrency regulation",
        target_audience="Crypto investors and financial enthusiasts",
        content_type="Opinion piece",
        additional_instructions="Focus on government overreach concerns and decentralization benefits.",
    )

    result = await pipeline.agenerate_content(params)

    log.info(f"Async pipeline completed for field: {result.field_of_topic}")
    log.info(f"Keywords used: {result.keywords}")
    log.info(f"Final content length: {len(result.final_content)} characters")
    log.info(
        f"Total pipeline tokens: {result.total_input_tokens} input, {result.total_output_tokens} output"
    )


def demo_with_different_models(model):
    """
    Demonstrate using different LLM models (when available).
    """
    log.info("=== Different Models Demo ===")

    # Example with different models (you can extend this based on available models)
    models = [
        ("GPT-4O-Mini", model),  # Reuse the existing model instance
        # Add more models as available in your setup
        # ("DeepSeek", DeepSeekLm(params=DeepSeekLmInitParams(model_name="deepseek-chat"))),
    ]

    field_of_topic = "Environment"
    keywords = "climate change mitigation strategies carbon footprint"

    for model_name, model_instance in models:
        log.info(f"Testing with {model_name}...")

        pipeline = ContentGenerationPipeline(model_instance)
        params = ContentGenerationPipelineParams(
            field_of_topic=field_of_topic,
            keywords=keywords,
            content_objectives="Create an educational article about climate change solutions",
            target_audience="General public interested in environmental issues",
            content_type="Educational article",
            # Use smaller token limits for demo
            discovery_max_tokens=2000,
            planning_max_tokens=1500,
            generation_max_tokens=2500,
        )

        result = pipeline.generate_content(params)

        log.info(f"{model_name} results:")
        log.info(f"  - Content length: {len(result.final_content)} characters")
        log.info(
            f"  - Tokens: {result.total_input_tokens} input, {result.total_output_tokens} output"
        )


def main():
    """
    Main function to run content generation demos.
    """
    # Load environment variables (for API keys)
    load_dotenv()

    log.info("Starting AI-driven Content Generation demos...")

    try:
        # Create a single model instance to avoid duplicate logger IDs
        model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))

        # Demo 1: Individual components
        demo_individual_components(model)

        log.info("\n" + "=" * 50 + "\n")

        # Demo 2: Complete pipeline
        demo_pipeline(model)

        log.info("\n" + "=" * 50 + "\n")

        # Demo 3: Async pipeline
        asyncio.run(demo_async_pipeline(model))

        log.info("\n" + "=" * 50 + "\n")

        # Demo 4: Different models
        demo_with_different_models(model)

        log.success("All content generation demos completed successfully!")

    except Exception as e:
        log.error(f"Error in content generation demo: {e}")
        raise


if __name__ == "__main__":
    main()
