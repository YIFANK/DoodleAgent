#!/usr/bin/env python3
"""
Test script for autonomous mood-based drawing functionality
This demonstrates the new autonomous mood-driven art creation feature.
"""

import os
import sys
from dotenv import load_dotenv
from free_drawing_agent import FreeDrawingAgent

# Load environment variables from .env file
load_dotenv()

def test_autonomous_mood_drawing():
    """Test the autonomous mood-based drawing functionality"""

    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        return

    # Initialize the agent
    agent = FreeDrawingAgent(api_key=api_key)

    print("🎨 Testing Autonomous Mood-Based Drawing")
    print("=" * 50)
    print("The AI will autonomously determine artistic moods for each test!")

    # Create output directory
    os.makedirs("output/autonomous_mood_test", exist_ok=True)

    # Test with a blank canvas (create a simple test image)
    test_canvas = "output/autonomous_mood_test/test_canvas.png"

    # Create a simple test canvas image if it doesn't exist
    if not os.path.exists(test_canvas):
        try:
            from PIL import Image, ImageDraw

            # Create a blank white canvas
            img = Image.new('RGB', (850, 500), color='white')
            draw = ImageDraw.Draw(img)

            # Add a simple border to make it look like a canvas
            draw.rectangle((0, 0, 849, 499), outline='gray', width=2)

            img.save(test_canvas)
            print(f"Created test canvas: {test_canvas}")

        except ImportError:
            print("PIL not available, using existing canvas if available...")
            if not os.path.exists("current_canvas.png"):
                print("No test canvas available. Please create a canvas image first.")
                return
            test_canvas = "current_canvas.png"

    # Test multiple autonomous mood generations
    num_tests = 5
    for test_num in range(num_tests):
        print(f"\n🎨 Autonomous Mood Test {test_num + 1}/{num_tests}")
        print("-" * 40)

        try:
            # Create autonomous mood-based drawing instruction
            instruction = agent.create_emotion_drawing_instruction(test_canvas)  # No mood parameter

            print(f"✅ Successfully generated autonomous mood instruction")
            print(f"   Brush: {instruction.brush}")
            print(f"   Color: {instruction.color}")
            print(f"   Strokes: {len(instruction.strokes)}")
            print(f"   Reasoning: {instruction.reasoning}")

            # Show stroke details
            for i, stroke in enumerate(instruction.strokes):
                print(f"   Stroke {i+1}: {stroke['description']}")
                print(f"     Points: {len(stroke['x'])} coordinates")
                print(f"     Timing: {stroke['t']}")

            # Save the instruction to a file
            import json
            output_file = f"output/autonomous_mood_test/autonomous_mood_{test_num + 1}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "test_number": test_num + 1,
                    "brush": instruction.brush,
                    "color": instruction.color,
                    "strokes": instruction.strokes,
                    "reasoning": instruction.reasoning
                }, f, indent=2)

            print(f"   📄 Instruction saved to: {output_file}")

        except Exception as e:
            print(f"❌ Error in autonomous mood test {test_num + 1}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n🎉 Autonomous mood testing completed!")
    print(f"Check the 'output/autonomous_mood_test' folder for detailed results.")

def test_single_autonomous_mood():
    """Test a single autonomous mood generation with detailed output"""

    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return

    # Initialize the agent
    agent = FreeDrawingAgent(api_key=api_key)

    print(f"🎨 Testing Single Autonomous Mood Generation")
    print("=" * 50)

    # Use existing canvas if available
    test_canvas = "current_canvas.png"
    if not os.path.exists(test_canvas):
        print(f"Canvas image not found: {test_canvas}")
        print("Please create a canvas image first or run the full demo.")
        return

    try:
        # Create autonomous mood-based drawing instruction
        instruction = agent.create_emotion_drawing_instruction(test_canvas)  # No mood parameter

        print(f"✅ Successfully generated autonomous mood instruction")
        print(f"\n📋 Instruction Details:")
        print(f"   Brush: {instruction.brush}")
        print(f"   Color: {instruction.color}")
        print(f"   Reasoning: {instruction.reasoning}")
        print(f"   Number of strokes: {len(instruction.strokes)}")

        print(f"\n🎨 Stroke Details:")
        for i, stroke in enumerate(instruction.strokes):
            print(f"   Stroke {i+1}: {stroke['description']}")
            print(f"     X coordinates: {stroke['x']}")
            print(f"     Y coordinates: {stroke['y']}")
            print(f"     Timing: {stroke['t']}")
            print()

        # Save the instruction
        import json
        output_file = f"output/autonomous_mood_detailed.json"
        os.makedirs("output", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump({
                "brush": instruction.brush,
                "color": instruction.color,
                "strokes": instruction.strokes,
                "reasoning": instruction.reasoning
            }, f, indent=2)

        print(f"📄 Detailed instruction saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error in autonomous mood generation: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function to run autonomous mood drawing tests"""

    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # Test a single autonomous mood generation
        test_single_autonomous_mood()
    else:
        # Test multiple autonomous mood generations
        test_autonomous_mood_drawing()

if __name__ == "__main__":
    main()
