#!/usr/bin/env python3
"""
Test script to demonstrate improved brush variety in the autonomous mood system
"""

import os
import sys
from dotenv import load_dotenv
from free_drawing_agent import FreeDrawingAgent
import json

# Load environment variables from .env file
load_dotenv()

def test_brush_variety():
    """Test that the system encourages brush variety"""

    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        return

    # Initialize the agent
    agent = FreeDrawingAgent(api_key=api_key)

    print("🎨 Testing Brush Variety System")
    print("=" * 50)
    print("Testing that the AI varies brush selection while maintaining mood consistency...")

    # Create output directory
    os.makedirs("output/brush_variety_test", exist_ok=True)

    # Create a blank test canvas
    test_canvas = "output/brush_variety_test/blank_canvas.png"

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

    # Test multiple autonomous mood generations to check brush variety
    num_tests = 8
    brushes_used = []
    moods_detected = []

    print(f"\n🎨 Running {num_tests} consecutive brush variety tests...")
    print("The AI should vary brush selection while maintaining mood consistency.")

    for test_num in range(num_tests):
        print(f"\n--- Test {test_num + 1}/{num_tests} ---")

        try:
            # Create autonomous mood-based drawing instruction
            instruction = agent.create_emotion_drawing_instruction(test_canvas)  # No mood parameter

            brush = instruction.brush
            brushes_used.append(brush)

            print(f"✅ Generated instruction")
            print(f"   Brush: {brush}")
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
                print(f"   🎭 Mood: {found_mood}")
                moods_detected.append(found_mood)

            # Show brush variety context
            if hasattr(agent, 'recent_brushes') and agent.recent_brushes:
                print(f"   📊 Recent brushes: {', '.join(agent.recent_brushes)}")

            # Save the instruction to a file
            output_file = f"output/brush_variety_test/brush_test_{test_num + 1}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "test_number": test_num + 1,
                    "brush": instruction.brush,
                    "color": instruction.color,
                    "strokes": instruction.strokes,
                    "reasoning": instruction.reasoning,
                    "mood_detected": found_mood,
                    "recent_brushes": agent.recent_brushes if hasattr(agent, 'recent_brushes') else []
                }, f, indent=2)

            print(f"   📄 Results saved to: {output_file}")

        except Exception as e:
            print(f"❌ Error in brush test {test_num + 1}: {e}")
            import traceback
            traceback.print_exc()

    # Analysis
    print(f"\n🎉 Brush Variety Analysis")
    print("=" * 50)
    print(f"Total tests: {num_tests}")
    print(f"Brushes used: {brushes_used}")
    print(f"Unique brushes: {len(set(brushes_used))}")
    print(f"Brush variety score: {len(set(brushes_used))}/{num_tests}")

    # Check for brush repetition
    brush_counts = {}
    for brush in brushes_used:
        brush_counts[brush] = brush_counts.get(brush, 0) + 1

    print(f"\nBrush usage breakdown:")
    for brush, count in brush_counts.items():
        percentage = (count / num_tests) * 100
        print(f"   {brush}: {count} times ({percentage:.1f}%)")

    # Evaluate variety
    if len(set(brushes_used)) >= 4:
        print("✅ Excellent brush variety!")
    elif len(set(brushes_used)) >= 3:
        print("✅ Good brush variety!")
    elif len(set(brushes_used)) >= 2:
        print("⚠️  Moderate brush variety - could be better")
    else:
        print("❌ Poor brush variety - system needs improvement")

    # Check for consecutive repetition
    consecutive_repetition = 0
    for i in range(1, len(brushes_used)):
        if brushes_used[i] == brushes_used[i-1]:
            consecutive_repetition += 1

    if consecutive_repetition == 0:
        print("✅ No consecutive brush repetition!")
    elif consecutive_repetition <= 2:
        print(f"⚠️  Some consecutive repetition: {consecutive_repetition} instances")
    else:
        print(f"❌ Too much consecutive repetition: {consecutive_repetition} instances")

    print(f"\nCheck the 'output/brush_variety_test' folder for detailed results.")

if __name__ == "__main__":
    test_brush_variety()
