#!/usr/bin/env python3
"""
Test script to verify that the autonomous mood system always starts with a mood
"""

import os
import sys
from dotenv import load_dotenv
from free_drawing_agent import FreeDrawingAgent
import json

# Load environment variables from .env file
load_dotenv()

def test_mood_always_starts():
    """Test that the system always starts with a mood determination"""

    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        return

    # Initialize the agent
    agent = FreeDrawingAgent(api_key=api_key)

    print("🎨 Testing Mood Always Starts")
    print("=" * 40)
    print("Verifying that the AI always determines a mood before drawing...")

    # Create output directory
    os.makedirs("output/mood_start_test", exist_ok=True)

    # Create a blank test canvas
    test_canvas = "output/mood_start_test/blank_canvas.png"

    try:
        from PIL import Image, ImageDraw

        # Create a blank white canvas
        img = Image.new('RGB', (850, 500), color='white')
        draw = ImageDraw.Draw(img)

        # Add a simple border to make it look like a canvas
        draw.rectangle((0, 0, 849, 499), outline='gray', width=2)

        img.save(test_canvas)
        print(f"Created blank test canvas: {test_canvas}")

    except ImportError:
        print("PIL not available, using existing canvas if available...")
        if not os.path.exists("current_canvas.png"):
            print("No test canvas available. Please create a canvas image first.")
            return
        test_canvas = "current_canvas.png"

    # Test multiple autonomous mood generations to verify mood is always present
    num_tests = 3
    moods_found = []

    for test_num in range(num_tests):
        print(f"\n🎨 Mood Test {test_num + 1}/{num_tests}")
        print("-" * 30)

        try:
            # Create autonomous mood-based drawing instruction
            instruction = agent.create_emotion_drawing_instruction(test_canvas)  # No mood parameter

            print(f"✅ Successfully generated instruction")
            print(f"   Brush: {instruction.brush}")
            print(f"   Reasoning: {instruction.reasoning}")

            # Check if reasoning mentions a mood
            reasoning_lower = instruction.reasoning.lower()
            mood_indicators = [
                "mood", "melancholic", "energetic", "chaotic", "serene", "bold",
                "gentle", "nostalgic", "mysterious", "joyful", "contemplative",
                "passionate", "tranquil", "dynamic", "peaceful", "intense", "calm",
                "whimsical", "dramatic", "subtle", "powerful", "delicate", "forceful",
                "dreamy", "vibrant", "somber", "lively", "meditative", "expressive"
            ]

            found_mood = None
            for mood in mood_indicators:
                if mood in reasoning_lower:
                    found_mood = mood
                    break

            if found_mood:
                print(f"   🎭 Mood detected: {found_mood}")
                moods_found.append(found_mood)
            else:
                print(f"   ⚠️  No specific mood detected in reasoning")

            # Save the instruction to a file
            output_file = f"output/mood_start_test/mood_test_{test_num + 1}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "test_number": test_num + 1,
                    "brush": instruction.brush,
                    "color": instruction.color,
                    "strokes": instruction.strokes,
                    "reasoning": instruction.reasoning,
                    "mood_detected": found_mood
                }, f, indent=2)

            print(f"   📄 Results saved to: {output_file}")

        except Exception as e:
            print(f"❌ Error in mood test {test_num + 1}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print(f"\n🎉 Mood Start Testing Summary")
    print("=" * 40)
    print(f"Tests completed: {num_tests}")
    print(f"Moods detected: {len(moods_found)}")

    if moods_found:
        print(f"Detected moods: {', '.join(moods_found)}")
        print("✅ System appears to be starting with moods!")
    else:
        print("⚠️  No moods detected - may need to check system prompt")

    print(f"\nCheck the 'output/mood_start_test' folder for detailed results.")

if __name__ == "__main__":
    test_mood_always_starts()
