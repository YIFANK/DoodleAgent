#!/usr/bin/env python3
"""
Test script for timing interpolation feature
This demonstrates how the timing field affects stroke interpolation.
"""

import json
from free_drawing_agent import FreeDrawingAgent
import os

def test_interpolation():
    """Test the interpolation function directly"""
    agent = FreeDrawingAgent("dummy_key", enable_logging=False)
    
    print("🧪 Testing Stroke Timing Interpolation")
    print("=" * 50)
    
    # Test case 1: Basic interpolation
    print("\n1. Basic Interpolation Test:")
    x_coords = [10, 20, 30, 40]
    y_coords = [10, 20, 30, 40]
    timing = [1, 2, 5]
    
    print(f"   Original: x={x_coords}, y={y_coords}")
    print(f"   Timing: {timing}")
    
    interp_x, interp_y = agent._interpolate_stroke_with_timing(x_coords, y_coords, timing)
    
    print(f"   Interpolated: x={interp_x}")
    print(f"   Interpolated: y={interp_y}")
    print(f"   Points: {len(x_coords)} → {len(interp_x)}")
    
    # Test case 2: Different timing values
    print("\n2. Different Timing Values:")
    test_cases = [
        ([0, 100], [0, 100], [1], "Quick (t=1)"),
        ([0, 100], [0, 100], [3], "Medium (t=3)"),
        ([0, 100], [0, 100], [5], "Slow (t=5)"),
    ]
    
    for x, y, t, description in test_cases:
        interp_x, interp_y = agent._interpolate_stroke_with_timing(x, y, t)
        print(f"   {description}: {len(x)} → {len(interp_x)} points")
        print(f"     Result: {interp_x}")
    
    # Test case 3: Complex stroke
    print("\n3. Complex Stroke (User's Example):")
    x_coords = [10, 20, 30, 40]
    y_coords = [10, 20, 30, 40]
    timing = [1, 2, 5]
    
    interp_x, interp_y = agent._interpolate_stroke_with_timing(x_coords, y_coords, timing)
    print(f"   Original: {x_coords}")
    print(f"   Timing: {timing}")
    print(f"   Result: {interp_x}")
    print(f"   Expected: [10, 20, 25, 30, 32, 34, 36, 38, 40]")
    print(f"   Match: {'✅' if interp_x == [10, 20, 25, 30, 32, 34, 36, 38, 40] else '❌'}")

def test_validation():
    """Test the validation function with timing"""
    agent = FreeDrawingAgent("dummy_key", enable_logging=False)
    
    print("\n🔧 Testing Validation with Timing")
    print("=" * 50)
    
    # Test valid stroke with timing
    test_data = {
        "brush": "rainbow",
        "strokes": [
            {
                "x": [100, 200, 300],
                "y": [100, 150, 100],
                "t": [3, 4],
                "description": "rainbow arc"
            }
        ],
        "reasoning": "Testing timing validation"
    }
    
    print("\n1. Valid stroke with timing:")
    print(f"   Input: {json.dumps(test_data, indent=4)}")
    
    validated = agent._validate_and_sanitize(test_data)
    stroke = validated["strokes"][0]
    
    print(f"   Original points: {len(stroke['original_x'])}")
    print(f"   Interpolated points: {len(stroke['x'])}")
    print(f"   Timing: {stroke['timing']}")
    print(f"   Final X: {stroke['x']}")
    
    # Test stroke missing timing
    print("\n2. Stroke missing timing (should auto-fill):")
    test_data_no_timing = {
        "brush": "pen",
        "strokes": [
            {
                "x": [50, 150, 250],
                "y": [50, 100, 50],
                "description": "no timing"
            }
        ],
        "reasoning": "Testing auto-fill timing"
    }
    
    validated = agent._validate_and_sanitize(test_data_no_timing)
    stroke = validated["strokes"][0]
    
    print(f"   Auto-filled timing: {stroke['timing']}")
    print(f"   Points: {len(stroke['original_x'])} → {len(stroke['x'])}")

def demo_creative_timing():
    """Demonstrate creative use of timing"""
    print("\n🎨 Creative Timing Examples")
    print("=" * 50)
    
    examples = [
        {
            "name": "Quick Outline",
            "x": [100, 200, 200, 100, 100],
            "y": [100, 100, 200, 200, 100],
            "t": [1, 1, 1, 1],
            "description": "Fast geometric outline"
        },
        {
            "name": "Smooth Curve",
            "x": [150, 200, 250, 300],
            "y": [200, 150, 150, 200],
            "t": [4, 5, 4],
            "description": "Slow artistic curve"
        },
        {
            "name": "Mixed Speed",
            "x": [50, 100, 150, 200, 250],
            "y": [250, 200, 250, 200, 250],
            "t": [1, 5, 1, 3],
            "description": "Variable speed zigzag"
        }
    ]
    
    agent = FreeDrawingAgent("dummy_key", enable_logging=False)
    
    for example in examples:
        print(f"\n{example['name']}:")
        print(f"   Description: {example['description']}")
        print(f"   Original points: {len(example['x'])}")
        print(f"   Timing: {example['t']}")
        
        interp_x, interp_y = agent._interpolate_stroke_with_timing(
            example['x'], example['y'], example['t']
        )
        
        print(f"   Interpolated points: {len(interp_x)}")
        print(f"   Speed profile: ", end="")
        
        # Show speed profile
        for i, t in enumerate(example['t']):
            speed_desc = {1: "Fast", 2: "Medium", 3: "Medium+", 4: "Slow", 5: "Very Slow"}
            print(f"Seg{i+1}:{speed_desc.get(t, 'Custom')}", end=" ")
        print()

def main():
    """Run all tests"""
    print("🚀 Timing Interpolation Test Suite")
    print("=" * 60)
    
    test_interpolation()
    test_validation() 
    demo_creative_timing()
    
    print("\n✅ All tests completed!")
    print("\nNow you can run the drawing agent with timing control:")
    print("  python demo_free_canvas.py")

if __name__ == "__main__":
    main() 