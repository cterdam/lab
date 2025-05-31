"""
Simple test script for the content generation pipeline.
This can be used to quickly test the implementation without running the full demo.
"""

from dotenv import load_dotenv

from src import log
from src.lib.model.txt.api.openai import (
    OpenaiLm,
    OpenaiLmInitParams,
)

from .interest_discovery import InterestDiscovery, InterestDiscoveryParams


def test_interest_discovery():
    """Test the interest discovery component."""
    print("Testing Interest Discovery Component...")

    # Load environment variables
    load_dotenv()

    # Initialize model
    model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))

    # Test interest discovery
    discovery = InterestDiscovery(model)
    params = InterestDiscoveryParams(
        field_of_topic="Technology",
        keywords="Python programming for beginners",
        max_tokens=1000,  # Small for testing
        temperature=0.7,
    )

    try:
        result = discovery.discover(params)
        print(f"✅ Interest Discovery successful!")
        print(f"   Field: {result.field_of_topic}")
        print(f"   Keywords: {result.keywords}")
        print(f"   Analysis length: {len(result.interest_analysis)} characters")
        print(f"   Tokens: {result.input_tokens} input, {result.output_tokens} output")
        print(f"   Preview: {result.interest_analysis[:200]}...")
        return True
    except Exception as e:
        print(f"❌ Interest Discovery failed: {e}")
        return False


def test_quick_pipeline():
    """Test a quick run of the full pipeline."""
    print("\nTesting Quick Pipeline...")

    try:
        from .pipeline import ContentGenerationPipeline, ContentGenerationPipelineParams

        # Load environment variables
        load_dotenv()

        # Initialize model and pipeline
        model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))
        pipeline = ContentGenerationPipeline(model)

        # Quick test with minimal tokens
        params = ContentGenerationPipelineParams(
            field_of_topic="Education",
            keywords="online learning effectiveness debate",
            content_objectives="Create a brief controversial article",
            target_audience="Educators",
            content_type="Opinion piece",
            discovery_max_tokens=800,
            planning_max_tokens=600,
            generation_max_tokens=1000,
        )

        result = pipeline.generate_content(params)
        print(f"✅ Quick Pipeline successful!")
        print(f"   Field: {result.field_of_topic}")
        print(f"   Keywords: {result.keywords}")
        print(f"   Final content length: {len(result.final_content)} characters")
        print(
            f"   Total tokens: {result.total_input_tokens} input, {result.total_output_tokens} output"
        )
        return True

    except Exception as e:
        print(f"❌ Quick Pipeline failed: {e}")
        return False


if __name__ == "__main__":
    print("Running Content Generation Pipeline Tests...\n")

    # Test individual component
    success1 = test_interest_discovery()

    # Test full pipeline
    success2 = test_quick_pipeline()

    if success1 and success2:
        print(f"\n🎉 All tests passed!")
    else:
        print(f"\n❌ Some tests failed. Check the output above.")
