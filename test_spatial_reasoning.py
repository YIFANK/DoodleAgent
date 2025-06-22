#!/usr/bin/env python3
"""
Test script to demonstrate the improved spatial reasoning with stroke history.
This shows how the agent now considers previous strokes when creating new ones.
"""

import os
from dotenv import load_dotenv
from free_drawing_agent import FreeDrawingAgent, DrawingInstruction

load_dotenv()

def test_spatial_reasoning():
    """Test the spatial reasoning functionality with mock strokes"""
    
    # Initialize agent with logging enabled
    agent = FreeDrawingAgent(api_key="test_key", enable_logging=False)
    
    print("🧪 Testing spatial reasoning with stroke history...")
    
    # Simulate a sequence of strokes to build up spatial context
    
    # Stroke 1: Draw a wavy line
    instruction1 = DrawingInstruction(
        brush="wiggle",
        color="#FF6B35",
        strokes=[{
            "x": [100, 150, 200, 250, 300],
            "y": [250, 230, 250, 230, 250],
            "original_x": [100, 150, 200, 250, 300],
            "original_y": [250, 230, 250, 230, 250],
            "t": [3, 3, 3, 3],
            "description": "playful wiggle line across center-left area"
        }],
        reasoning="Starting with a playful wiggle line to bring some cheerful energy to the blank canvas"
    )
    
    agent._track_stroke_history(instruction1)
    print(f"✅ Tracked stroke 1: {instruction1.reasoning}")
    
    # Stroke 2: Add another element
    instruction2 = DrawingInstruction(
        brush="pen",
        color="#2E86AB",
        strokes=[{
            "x": [350, 400, 450],
            "y": [200, 180, 200],
            "original_x": [350, 400, 450],
            "original_y": [200, 180, 200],
            "t": [2, 2],
            "description": "curved line in top-center area"
        }],
        reasoning="Adding a curved line in the upper region to create visual balance"
    )
    
    agent._track_stroke_history(instruction2)
    print(f"✅ Tracked stroke 2: {instruction2.reasoning}")
    
    # Now show the spatial context that would be provided to the next stroke
    context = agent._get_stroke_history_context()
    print("\n" + "="*60)
    print("SPATIAL CONTEXT FOR NEXT STROKE:")
    print("="*60)
    print(context)
    
    # Demonstrate how this would help with the "bird on wavy line" scenario
    print("\n" + "="*60)
    print("EXAMPLE: How this helps with 'bird on wavy line' scenario:")
    print("="*60)
    print("❌ Before: Agent had no knowledge of the wavy line's position")
    print("✅ Now: Agent knows:")
    print("   - Wavy line is in center-left (100-300 x, 230-250 y)")
    print("   - To place a bird 'on' the line, use Y coordinates ~230-250")
    print("   - Can position bird at any X between 100-300 to sit on the line")
    print("   - Should consider existing curves when drawing bird shape")
    
    print(f"\n🎯 Stroke history contains {len(agent.stroke_history)} strokes")
    print("✅ Spatial reasoning test completed!")

if __name__ == "__main__":
    test_spatial_reasoning() 