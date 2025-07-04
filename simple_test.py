#!/usr/bin/env python3
"""
Simple test for JSON format validation without browser
"""

import json
import random

def generate_test_json():
    """Generate a test JSON matching the required format"""
    
    # Create a simple drawing instruction
    instruction = {
        "thinking": "I'll draw a simple line across the canvas using a marker brush.",
        "brush": "marker",
        "color": "#FF0000",
        "strokes": [
            {
                "x": [100, 200, 300, 400],
                "y": [150, 160, 140, 155]
            }
        ]
    }
    
    return instruction

def validate_json_format(json_data):
    """Validate that JSON matches the required format"""
    print("Validating JSON format...")
    
    # Check required top-level fields
    required_fields = ["thinking", "brush", "color", "strokes"]
    for field in required_fields:
        if field not in json_data:
            print(f"❌ Missing required field: {field}")
            return False
        print(f"✅ Found field: {field}")
    
    # Check strokes format
    if not isinstance(json_data["strokes"], list):
        print("❌ 'strokes' must be a list")
        return False
    
    if len(json_data["strokes"]) == 0:
        print("❌ 'strokes' list cannot be empty")
        return False
    
    # Check each stroke
    for i, stroke in enumerate(json_data["strokes"]):
        print(f"  Checking stroke {i+1}...")
        
        if not isinstance(stroke, dict):
            print(f"❌ Stroke {i+1} must be a dictionary")
            return False
        
        if "x" not in stroke or "y" not in stroke:
            print(f"❌ Stroke {i+1} missing 'x' or 'y' coordinates")
            return False
        
        if not isinstance(stroke["x"], list) or not isinstance(stroke["y"], list):
            print(f"❌ Stroke {i+1} coordinates must be lists")
            return False
        
        if len(stroke["x"]) != len(stroke["y"]):
            print(f"❌ Stroke {i+1} has mismatched x/y coordinate lengths")
            return False
        
        if len(stroke["x"]) < 2:
            print(f"❌ Stroke {i+1} needs at least 2 points")
            return False
        
        print(f"  ✅ Stroke {i+1} valid ({len(stroke['x'])} points)")
    
    print("✅ JSON format validation passed!")
    return True

def main():
    print("Simple JSON Format Test")
    print("=" * 30)
    
    # Generate test JSON
    test_json = generate_test_json()
    
    print("\nGenerated JSON:")
    print(json.dumps(test_json, indent=2))
    
    print("\n" + "=" * 30)
    
    # Validate format
    is_valid = validate_json_format(test_json)
    
    if is_valid:
        print("\n🎉 Test passed! JSON format is correct.")
        print("\nThis JSON can be used with drawing_canvas_bridge.py")
    else:
        print("\n❌ Test failed! JSON format is incorrect.")
    
    return is_valid

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 