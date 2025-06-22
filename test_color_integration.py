#!/usr/bin/env python3
"""
Test script to verify color integration in the drawing agent.
"""

import json
from free_drawing_agent import FreeDrawingAgent
import os
from dotenv import load_dotenv

load_dotenv()

def test_color_validation():
    """Test that color validation works correctly"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return

    agent = FreeDrawingAgent(api_key=api_key, enable_logging=False)

    # Test data with different brush and color combinations
    test_cases = [
        {
            "name": "Valid marker with color",
            "data": {
                "brush": "marker",
                "color": "#ff0000",
                "strokes": [{"x": [100, 200], "y": [100, 200], "t": [2], "description": "red line"}],
                "reasoning": "Testing red marker"
            }
        },
        {
            "name": "Valid crayon with color",
            "data": {
                "brush": "crayon", 
                "color": "#00ff00",
                "strokes": [{"x": [100, 200], "y": [100, 200], "t": [2], "description": "green line"}],
                "reasoning": "Testing green crayon"
            }
        },
        {
            "name": "Valid wiggle with color",
            "data": {
                "brush": "wiggle",
                "color": "#0000ff", 
                "strokes": [{"x": [100, 200], "y": [100, 200], "t": [2], "description": "blue wiggle"}],
                "reasoning": "Testing blue wiggle"
            }
        },
        {
            "name": "Pen with color (should use default)",
            "data": {
                "brush": "pen",
                "color": "#ff0000",
                "strokes": [{"x": [100, 200], "y": [100, 200], "t": [2], "description": "pen line"}],
                "reasoning": "Testing pen with color"
            }
        },
        {
            "name": "Invalid color format (should use default)",
            "data": {
                "brush": "marker",
                "color": "red",
                "strokes": [{"x": [100, 200], "y": [100, 200], "t": [2], "description": "marker line"}],
                "reasoning": "Testing invalid color"
            }
        }
    ]

    print("🎨 Testing Color Validation")
    print("=" * 50)

    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        
        # Test regular validation
        validated = agent._validate_and_sanitize(test_case['data'])
        print(f"   Brush: {validated['brush']}")
        print(f"   Color: {validated['color']}")
        
        # Test emotion validation
        emotion_validated = agent._validate_and_sanitize_emotion(test_case['data'], "happy")
        print(f"   Emotion Color: {emotion_validated['color']}")
        
        # Test abstract validation
        abstract_validated = agent._validate_and_sanitize_abstract(test_case['data'])
        print(f"   Abstract Color: {abstract_validated['color']}")

    print("\n✅ Color validation tests completed!")

def test_color_integration_info():
    """Print information about the color integration"""
    print("\n🌈 Color Integration Summary")
    print("=" * 50)
    
    print("📝 Updated Features:")
    print("   • Marker brush now supports custom colors")
    print("   • Crayon brush now supports custom colors")
    print("   • Wiggle brush now supports custom colors")
    print("   • Pen, spray, and fountain brushes remain black")
    
    print("\n🎯 JSON Output Format:")
    example_json = {
        "brush": "marker",
        "color": "#ff6b6b",
        "strokes": [
            {
                "x": [100, 200, 300],
                "y": [100, 150, 200],
                "t": [2, 3],
                "description": "curved line"
            }
        ],
        "reasoning": "Drawing with custom color"
    }
    print(json.dumps(example_json, indent=2))
    
    print("\n🔧 Bridge Integration:")
    print("   • set_brush() method now accepts color parameter")
    print("   • set_brush_color() method added for color pickers")
    print("   • Color validation ensures proper hex format")
    print("   • Fallback colors provided for invalid input")

if __name__ == "__main__":
    test_color_validation()
    test_color_integration_info()
    print("\n🎉 All tests completed!") 