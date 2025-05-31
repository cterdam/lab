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

from .background_discovery import BackgroundDiscovery, BackgroundDiscoveryParams


def test_background_discovery():
    """Test the background discovery component."""
    print("Testing Background Discovery Component...")

    # Load environment variables
    load_dotenv()

    # Initialize model
    model = OpenaiLm(params=OpenaiLmInitParams(model_name="gpt-4o-mini"))

    # Test background discovery
    discovery = BackgroundDiscovery(model)
    params = BackgroundDiscoveryParams(
        topic="Python programming for beginners",
        max_tokens=1000,  # Small for testing
        temperature=0.3,
    )

    try:
        result = discovery.discover(params)
        print(f"✅ Background Discovery successful!")
        print(f"   Topic: {result.topic}")
        print(f"   Research length: {len(result.background_research)} characters")
        print(f"   Tokens: {result.input_tokens} input, {result.output_tokens} output")
        print(f"   Preview: {result.background_research[:200]}...")
        return True
    except Exception as e:
        print(f"❌ Background Discovery failed: {e}")
        return False


if __name__ == "__main__":
    test_background_discovery()
