#!/usr/bin/env python3
"""
Quick test to verify abstract mode uses different brushes
"""

import os
from dotenv import load_dotenv
from free_drawing_agent import FreeDrawingAgent
from PIL import Image, ImageDraw

# Load environment variables
load_dotenv()

def test_abstract_brush_variety():
    """Test that abstract mode uses different brushes"""

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return False

    print("🧪 Testing Abstract Mode Brush Variety")
    print("=" * 50)

    # Create a test canvas
    test_canvas_path = "test_abstract_variety.png"
    img = Image.new('RGB', (850, 500), color='#fbf8f3')
    draw = ImageDraw.Draw(img)
    draw.rectangle((100, 100, 200, 200), outline='black', width=2)
    img.save(test_canvas_path)

    # Initialize agent
    agent = FreeDrawingAgent(api_key=api_key, enable_logging=True)

    # Test multiple abstract instructions
    brushes_used = []

    for i in range(3):
        print(f"\n🎨 Abstract instruction {i+1}...")

        try:
            instruction = agent.create_abstract_drawing_instruction(test_canvas_path)
            brushes_used.append(instruction.brush)

            print(f"Brush: {instruction.brush}")
            print(f"Reasoning: {instruction.reasoning[:100]}...")

        except Exception as e:
            print(f"Error: {e}")
            brushes_used.append("error")

    # Analyze results
    print(f"\n📊 Brush Usage Analysis:")
    print(f"Brushes used: {brushes_used}")

    unique_brushes = set(brushes_used)
    print(f"Unique brushes: {len(unique_brushes)} out of {len(brushes_used)}")

    if len(unique_brushes) > 1:
        print("✅ Abstract mode is using different brushes!")
    else:
        print("⚠️ Abstract mode may be stuck on one brush")

    # Check if rainbow is overused
    rainbow_count = brushes_used.count("rainbow")
    if rainbow_count > 1:
        print(f"⚠️ Rainbow brush used {rainbow_count} times - may be overused")
    else:
        print("✅ Rainbow brush usage is reasonable")

    # Clean up
    if os.path.exists(test_canvas_path):
        os.remove(test_canvas_path)

    return len(unique_brushes) > 1

if __name__ == "__main__":
    success = test_abstract_brush_variety()
    if success:
        print("\n🎉 Abstract brush variety test passed!")
    else:
        print("\n⚠️ Abstract brush variety test failed!")
