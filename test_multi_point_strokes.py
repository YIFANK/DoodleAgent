#!/usr/bin/env python3
"""
Test script for multi-point stroke functionality.
This script tests the enhanced stroke system that creates continuous strokes
from multiple points instead of individual dots.
"""

import json
from drawing_agent import DrawingAgent, DrawingAction

def test_multi_point_strokes():
    """Test the multi-point stroke enhancement"""
    
    # Create a test agent (without API key for testing)
    agent = DrawingAgent(api_key="test")
    
    # Test data with single points
    test_strokes = [
        {"x": 100, "y": 100, "description": "Single point 1"},
        {"x": 200, "y": 150, "description": "Single point 2"},
        {"x": 300, "y": 200, "description": "Single point 3"}
    ]
    
    # Test data with multi-point strokes
    test_multi_strokes = [
        {"x": [100, 110, 120, 130, 140], "y": [100, 105, 110, 115, 120], "description": "Multi-point stroke 1"},
        {"x": [200, 210, 220, 230, 240], "y": [150, 155, 160, 165, 170], "description": "Multi-point stroke 2"}
    ]
    
    # Test data with mixed strokes
    test_mixed_strokes = [
        {"x": 100, "y": 100, "description": "Single point"},
        {"x": [200, 210, 220, 230, 240], "y": [150, 155, 160, 165, 170], "description": "Multi-point stroke"},
        {"x": 300, "y": 200, "description": "Another single point"}
    ]
    
    print("Testing multi-point stroke enhancement...")
    print("=" * 50)
    
    # Test single points
    print("\n1. Testing single points:")
    enhanced_single = agent._enhance_strokes(test_strokes)
    for i, stroke in enumerate(enhanced_single):
        print(f"  Stroke {i+1}: {stroke['x']} -> {stroke['x']}")
        print(f"           {stroke['y']} -> {stroke['y']}")
    
    # Test multi-point strokes
    print("\n2. Testing multi-point strokes:")
    enhanced_multi = agent._enhance_strokes(test_multi_strokes)
    for i, stroke in enumerate(enhanced_multi):
        print(f"  Stroke {i+1}: {stroke['x']} (unchanged)")
        print(f"           {stroke['y']} (unchanged)")
    
    # Test mixed strokes
    print("\n3. Testing mixed strokes:")
    enhanced_mixed = agent._enhance_strokes(test_mixed_strokes)
    for i, stroke in enumerate(enhanced_mixed):
        print(f"  Stroke {i+1}: {stroke['x']}")
        print(f"           {stroke['y']}")
    
    print("\n" + "=" * 50)
    print("Multi-point stroke enhancement test completed!")

def test_stroke_validation():
    """Test stroke validation and brush type validation"""
    
    agent = DrawingAgent(api_key="test")
    
    print("\nTesting brush type validation...")
    print("=" * 30)
    
    test_brushes = ["flowing", "watercolor", "crayon", "oil", "particle", "water", "paint", "invalid"]
    
    for brush in test_brushes:
        validated = agent._validate_brush_type(brush)
        print(f"  '{brush}' -> '{validated}'")
    
    print("\nBrush validation test completed!")

if __name__ == "__main__":
    test_multi_point_strokes()
    test_stroke_validation() 