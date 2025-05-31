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

from .background_discovery import BackgroundDiscovery, BackgroundDiscoveryParams
from .draft_generation import DraftGeneration, DraftGenerationParams
from .pipeline import ContentGenerationPipeline, ContentGenerationPipelineParams
from .structural_planning import StructuralPlanning, StructuralPlanningParams


def demo_individual_components(model):
    """
    Demonstrate using each component individually with provided model.
    """
    log.info("=== Individual Components Demo ===")

    topic = "The future of renewable energy"

    # Component 1: Background Discovery
    log.info("Running Background Discovery...")
    discovery = BackgroundDiscovery(model)
    discovery_params = BackgroundDiscoveryParams(topic=topic)
    discovery_result = discovery.discover(discovery_params)

    log.info(
        f"Background research generated: {len(discovery_result.background_research)} characters"
    )
    log.info(
        f"Discovery tokens: {discovery_result.input_tokens} input, {discovery_result.output_tokens} output"
    )

    # Component 2: Structural Planning
    log.info("Running Structural Planning...")
    planning = StructuralPlanning(model)
    planning_params = StructuralPlanningParams(
        background_research=discovery_result.background_research,
        content_objectives="Create an informative article about renewable energy for business leaders",
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
        background_research=discovery_result.background_research,
        structural_plan=planning_result.structural_plan,
        additional_instructions="Write in a professional but accessible tone. Include specific examples and actionable insights.",
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
    log.success(
        f"Individual components completed. Total tokens: {total_input} input, {total_output} output"
    )


def demo_complete_pipeline(model):
    """
    Demonstrate using the complete pipeline with provided model.
    """
    log.info("=== Complete Pipeline Demo ===")

    # Initialize pipeline
    pipeline = ContentGenerationPipeline(model)

    # Configure pipeline parameters
    params = ContentGenerationPipelineParams(
        topic="Artificial Intelligence in Healthcare",
        content_objectives="Create a comprehensive guide that explains AI applications in healthcare for medical professionals",
        target_audience="Healthcare professionals, doctors, and medical administrators",
        content_type="Educational guide",
        additional_instructions="Focus on practical applications, ethical considerations, and future prospects. Use medical terminology appropriately but ensure accessibility.",
        # Customize token limits and temperatures for each component
        discovery_max_tokens=3500,
        discovery_temperature=0.2,  # More factual
        planning_max_tokens=2500,
        planning_temperature=0.4,  # Balanced
        generation_max_tokens=4500,
        generation_temperature=0.7,  # More creative
    )

    # Generate content
    result = pipeline.generate_content(params)

    # Display results
    log.info(f"Topic: {result.topic}")
    log.info(f"Content Type: {result.content_type}")
    log.info(f"Target Audience: {result.target_audience}")
    log.info(f"Final content length: {len(result.final_content)} characters")
    log.info(
        f"Total tokens: {result.total_input_tokens} input, {result.total_output_tokens} output"
    )

    # Save the final content for review
    content_preview = (
        result.final_content[:500] + "..."
        if len(result.final_content) > 500
        else result.final_content
    )
    log.info(f"Content preview:\n{content_preview}")

    log.success("Complete pipeline demo completed successfully!")

    return result


async def demo_async_pipeline(model):
    """
    Demonstrate using the async pipeline for better performance with provided model.
    """
    log.info("=== Async Pipeline Demo ===")

    # Initialize pipeline
    pipeline = ContentGenerationPipeline(model)

    # Configure parameters for multiple topics
    topics = [
        {
            "topic": "Sustainable Agriculture Practices",
            "objectives": "Create an informative article about sustainable farming for farmers and agricultural businesses",
            "audience": "Farmers, agricultural professionals, and sustainability experts",
            "type": "Technical article",
        },
        {
            "topic": "Remote Work Best Practices",
            "objectives": "Create a practical guide for effective remote work management",
            "audience": "Managers, team leaders, and remote workers",
            "type": "Practical guide",
        },
    ]

    # Generate content for multiple topics asynchronously
    tasks = []
    for topic_config in topics:
        params = ContentGenerationPipelineParams(
            topic=topic_config["topic"],
            content_objectives=topic_config["objectives"],
            target_audience=topic_config["audience"],
            content_type=topic_config["type"],
        )
        tasks.append(pipeline.agenerate_content(params))

    # Wait for all to complete
    results = await asyncio.gather(*tasks)

    # Display results
    for i, result in enumerate(results, 1):
        log.info(f"Result {i}: {result.topic}")
        log.info(f"  - Content length: {len(result.final_content)} characters")
        log.info(
            f"  - Tokens: {result.total_input_tokens} input, {result.total_output_tokens} output"
        )

    total_input = sum(r.total_input_tokens for r in results)
    total_output = sum(r.total_output_tokens for r in results)
    log.success(
        f"Async pipeline demo completed! Total: {total_input} input, {total_output} output tokens"
    )

    return results


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

    topic = "Climate Change Mitigation Strategies"

    for model_name, model_instance in models:
        log.info(f"Testing with {model_name}...")

        pipeline = ContentGenerationPipeline(model_instance)
        params = ContentGenerationPipelineParams(
            topic=topic,
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
        result = demo_complete_pipeline(model)

        log.info("\n" + "=" * 50 + "\n")

        # Demo 3: Async pipeline
        asyncio.run(demo_async_pipeline(model))

        log.info("\n" + "=" * 50 + "\n")

        # Demo 4: Different models
        demo_with_different_models(model)

        log.success("All content generation demos completed successfully!")

        # Return one result for inspection
        return result

    except Exception as e:
        log.error(f"Error in content generation demo: {e}")
        raise


if __name__ == "__main__":
    main()
