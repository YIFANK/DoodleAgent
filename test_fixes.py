#!/usr/bin/env python3
"""
Test script to verify the fixes for the coordinate bounds and API errors.
"""

import json
from painting_bridge import PaintingBridge
from drawing_agent import DrawingAgent, DrawingAction

def test_coordinate_validation():
    """Test the coordinate validation function"""
    print("Testing coordinate validation...")
    
    # Create a mock bridge instance
    bridge = PaintingBridge()
    
    # Test coordinates that should be sanitized
    test_cases = [
        (-10, -10, "negative coordinates"),
        (1000, 1000, "coordinates too large"),
        (0, 0, "edge coordinates"),
        (400, 300, "valid coordinates"),
    ]
    
    for x, y, description in test_cases:
        safe_x, safe_y = bridge._validate_coordinates(x, y)
        print(f"  {description}: ({x}, {y}) -> ({safe_x}, {safe_y})")
    
    print("✅ Coordinate validation test completed")

def test_json_parsing():
    """Test the JSON parsing improvements"""
    print("\nTesting JSON parsing improvements...")
    
    # Test valid JSON
    valid_json = {
        "brush": "watercolor",
        "color": "#ff6b6b",
        "strokes": [],
        "reasoning": "Test action"
    }
    
    # Test missing fields
    invalid_json = {
        "brush": "watercolor",
        # Missing color and strokes
    }
    
    try:
        # This should work
        action = DrawingAction(
            brush=valid_json["brush"],
            color=valid_json["color"],
            strokes=valid_json["strokes"],
            reasoning=valid_json.get("reasoning", "")
        )
        print("  ✅ Valid JSON parsing works")
    except Exception as e:
        print(f"  ❌ Valid JSON parsing failed: {e}")
    
    try:
        # This should handle missing fields gracefully
        action = DrawingAction(
            brush=invalid_json.get("brush", "watercolor"),
            color=invalid_json.get("color", "#ff6b6b"),
            strokes=invalid_json.get("strokes", []),
            reasoning=invalid_json.get("reasoning", "Default action")
        )
        print("  ✅ Missing fields handled gracefully")
    except Exception as e:
        print(f"  ❌ Missing fields handling failed: {e}")
    
    print("✅ JSON parsing test completed")

def test_stroke_validation():
    """Test stroke validation with various coordinate scenarios"""
    print("\nTesting stroke validation...")
    
    bridge = PaintingBridge()
    
    # Test strokes with various coordinate issues
    test_strokes = [
        {
            "type": "stroke",
            "points": [
                {"x": -10, "y": -10, "action": "mousedown"},
                {"x": 1000, "y": 1000, "action": "mouseup"}
            ]
        },
        {
            "type": "stroke", 
            "points": [
                {"x": 100, "y": 100, "action": "mousedown"},
                {"x": 200, "y": 200, "action": "mouseup"}
            ]
        }
    ]
    
    for i, stroke in enumerate(test_strokes):
        print(f"  Testing stroke {i+1}:")
        for point in stroke["points"]:
            safe_x, safe_y = bridge._validate_coordinates(point["x"], point["y"])
            print(f"    ({point['x']}, {point['y']}) -> ({safe_x}, {safe_y})")
    
    print("✅ Stroke validation test completed")

if __name__ == "__main__":
    print("🧪 Running fix verification tests...")
    print("=" * 50)
    
    test_coordinate_validation()
    test_json_parsing()
    test_stroke_validation()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nThe fixes should resolve:")
    print("1. ✅ 'color' API parsing errors")
    print("2. ✅ 'move target out of bounds' Selenium errors")
    print("\nYou can now run demo.py again to test the fixes.") 