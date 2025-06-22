#!/usr/bin/env python3
"""
Test script for Abstract Drawing Mode
This script tests the new abstract drawing functionality that creates
non-representational, pure abstract art.
"""

import os
import sys
from dotenv import load_dotenv
from free_drawing_agent import FreeDrawingAgent
import json

# Load environment variables from .env file
load_dotenv()

def test_abstract_drawing():
    """Test the abstract drawing functionality"""

    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        return False

    print("🧪 Testing Abstract Drawing Mode")
    print("=" * 50)

    # Initialize the agent
    agent = FreeDrawingAgent(api_key=api_key, enable_logging=True)

    # Test with a blank canvas (create a simple test image)
    test_canvas_path = "test_abstract_canvas.png"

    # Create a simple test canvas if it doesn't exist
    if not os.path.exists(test_canvas_path):
        from PIL import Image, ImageDraw

        # Create a blank canvas
        img = Image.new('RGB', (850, 500), color='#fbf8f3')
        draw = ImageDraw.Draw(img)

        # Add a simple test element to make it non-blank
        draw.rectangle((100, 100, 200, 200), outline='black', width=2)

        img.save(test_canvas_path)
        print(f"Created test canvas: {test_canvas_path}")

    print(f"Testing with canvas: {test_canvas_path}")

    # Test abstract drawing instruction
    try:
        print("\n🎨 Creating abstract drawing instruction...")
        instruction = agent.create_abstract_drawing_instruction(test_canvas_path)

        print("\n✅ Abstract drawing instruction created successfully!")
        print(f"Brush: {instruction.brush}")
        print(f"Color: {instruction.color}")
        print(f"Number of strokes: {len(instruction.strokes)}")
        print(f"Reasoning: {instruction.reasoning}")

        # Validate the instruction
        print("\n🔍 Validating instruction...")

        # Check if brush is valid
        valid_brushes = ["pen", "marker", "rainbow", "wiggle", "spray", "fountain"]
        if instruction.brush not in valid_brushes:
            print(f"❌ Invalid brush: {instruction.brush}")
            return False
        else:
            print(f"✅ Valid brush: {instruction.brush}")

        # Check if strokes are valid
        if not instruction.strokes:
            print("❌ No strokes in instruction")
            return False

        print(f"✅ {len(instruction.strokes)} strokes found")

        # Check each stroke
        for i, stroke in enumerate(instruction.strokes):
            print(f"\n📝 Stroke {i+1}:")

            if "x" not in stroke or "y" not in stroke:
                print(f"❌ Stroke {i+1} missing x or y coordinates")
                return False

            x_coords = stroke["x"]
            y_coords = stroke["y"]

            if len(x_coords) != len(y_coords):
                print(f"❌ Stroke {i+1} has mismatched x/y coordinate counts")
                return False

            if len(x_coords) < 2:
                print(f"❌ Stroke {i+1} has insufficient points")
                return False

            print(f"✅ {len(x_coords)} points, description: {stroke.get('description', 'No description')}")

        # Check reasoning for abstract keywords
        reasoning_lower = instruction.reasoning.lower()
        abstract_keywords = ["abstract", "non-representational", "pure", "geometric", "organic", "flow", "pattern", "shape", "line"]

        has_abstract_keywords = any(keyword in reasoning_lower for keyword in abstract_keywords)
        if has_abstract_keywords:
            print(f"✅ Reasoning contains abstract keywords")
        else:
            print(f"⚠️ Reasoning may not be abstract-focused: {instruction.reasoning}")

        print("\n🎉 Abstract drawing test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error during abstract drawing test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_abstract_vs_concrete():
    """Test that abstract mode avoids concrete objects"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return False

    print("\n🧪 Testing Abstract vs Concrete Detection")
    print("=" * 50)

    agent = FreeDrawingAgent(api_key=api_key, enable_logging=True)

    # Test with a canvas that has some concrete elements
    test_canvas_path = "test_concrete_canvas.png"

    # Create a canvas with concrete elements
    from PIL import Image, ImageDraw

    img = Image.new('RGB', (850, 500), color='#fbf8f3')
    draw = ImageDraw.Draw(img)

    # Add some concrete elements
    draw.ellipse((200, 150, 300, 250), outline='black', width=2)  # Circle (could be interpreted as face/sun)
    draw.rectangle((400, 200, 500, 300), outline='black', width=2)  # Rectangle (could be interpreted as building)

    img.save(test_canvas_path)
    print(f"Created canvas with concrete elements: {test_canvas_path}")

    try:
        print("\n🎨 Creating abstract drawing instruction on canvas with concrete elements...")
        instruction = agent.create_abstract_drawing_instruction(test_canvas_path)

        print(f"\n✅ Abstract instruction created!")
        print(f"Reasoning: {instruction.reasoning}")

        # Check if the reasoning emphasizes abstract concepts
        reasoning_lower = instruction.reasoning.lower()

        abstract_indicators = [
            "abstract", "non-representational", "pure", "geometric",
            "organic", "flow", "pattern", "shape", "line", "energy",
            "movement", "rhythm", "texture", "color", "form"
        ]

        concrete_indicators = [
            "object", "thing", "animal", "person", "building", "house",
            "tree", "flower", "car", "face", "body", "realistic"
        ]

        abstract_score = sum(1 for keyword in abstract_indicators if keyword in reasoning_lower)
        concrete_score = sum(1 for keyword in concrete_indicators if keyword in reasoning_lower)

        print(f"\n📊 Analysis:")
        print(f"Abstract indicators found: {abstract_score}")
        print(f"Concrete indicators found: {concrete_score}")

        if abstract_score > concrete_score:
            print("✅ Abstract mode successfully focuses on abstract concepts!")
        else:
            print("⚠️ Abstract mode may need refinement to avoid concrete references")

        return True

    except Exception as e:
        print(f"❌ Error during abstract vs concrete test: {e}")
        return False

def main():
    """Run all abstract drawing tests"""
    print("🎨 Abstract Drawing Mode Test Suite")
    print("=" * 60)

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # Run tests
    test1_success = test_abstract_drawing()
    test2_success = test_abstract_vs_concrete()

    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    print(f"Abstract Drawing Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Abstract vs Concrete Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")

    if test1_success and test2_success:
        print("\n🎉 All tests passed! Abstract drawing mode is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")

    # Clean up test files
    for test_file in ["test_abstract_canvas.png", "test_concrete_canvas.png"]:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"Cleaned up: {test_file}")

if __name__ == "__main__":
    main()
