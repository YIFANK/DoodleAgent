#!/usr/bin/env python3
"""
Test script for complex response extraction.
This script tests the ability to extract drawing information from complex API responses.
"""

from drawing_agent import DrawingAgent

def test_complex_response_extraction():
    """Test extraction from complex API responses"""
    
    # Create a test agent
    agent = DrawingAgent(api_key="test")
    
    # Test complex responses that the agent might return
    complex_responses = [
        # Response with nested colors object
        '''{
            "brush": "watercolor",
            "colors": {
                "darkGreen": "#2E8B57",
                "mediumGreen": "#3CB371",
                "lightGreen": "#90EE90"
            },
            "strokes": [
                {
                    "x": [50, 150, 300, 450, 600, 750],
                    "y": [500, 480, 450, 470, 490, 510],
                    "description": "Create undulating hill base line",
                    "color": "#2E8B57"
                }
            ],
            "reasoning": "Creating layered, rolling hills"
        }''',
        
        # Response with brush as array
        '''{
            "brush": ["watercolor", "particle"],
            "colors": {
                "red": "#FF4500",
                "orange": "#FF6347"
            },
            "particleEffects": [
                {
                    "origin": {"x": 300, "y": 650},
                    "direction": "upward",
                    "count": 200
                }
            ],
            "reasoning": "Creating dynamic particle effects"
        }''',
        
        # Response with missing required fields
        '''{
            "brush": "oil",
            "dabs": [
                {
                    "type": "impasto",
                    "points": [
                        {"x": 250, "y": 400, "size": 25}
                    ],
                    "colors": ["#FFD700", "#FFA500"]
                }
            ],
            "reasoning": "Adding vibrant yellow oil paint dabs"
        }''',
        
        # Malformed response
        '''{
            "brush": "crayon",
            "color": "#000000",
            "strokes": "invalid_strokes_format",
            "reasoning": "Adding bold black crayon strokes"
        }'''
    ]
    
    print("Testing complex response extraction...")
    print("=" * 60)
    
    for i, response in enumerate(complex_responses, 1):
        print(f"\nTest {i}:")
        print(f"Input: {response[:100]}...")
        
        # Test validation
        try:
            import json
            parsed = json.loads(response)
            is_valid = agent._validate_action_data(parsed)
            print(f"Valid format: {is_valid}")
            
            if not is_valid:
                extracted = agent._extract_from_complex_response(response)
                print(f"Extracted: {extracted}")
                
                if extracted:
                    # Test brush validation
                    validated_brush = agent._validate_brush_type(extracted["brush"])
                    print(f"Brush validation: {extracted['brush']} -> {validated_brush}")
                    
                    # Test stroke enhancement
                    enhanced_strokes = agent._enhance_strokes(extracted["strokes"])
                    print(f"Strokes enhanced: {len(enhanced_strokes)} strokes")
                    
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)
    print("Complex response extraction test completed!")

if __name__ == "__main__":
    test_complex_response_extraction() 