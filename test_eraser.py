#!/usr/bin/env python3
"""
Test script to demonstrate eraser functionality in the DoodleAgent.
This script will first draw some elements and then use the eraser to clean them up.
"""

import os
from dotenv import load_dotenv
from painting_bridge import AutomatedPainter

# Load environment variables
load_dotenv()

def test_eraser_functionality():
    """Test the eraser functionality with the drawing agent"""
    
    # Get API key from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found in environment variables")
        return
    
    # Initialize the automated painter
    painter_url = f"file://{os.path.abspath('painter.html')}"
    painter = AutomatedPainter(api_key=api_key, painter_url=painter_url)
    
    try:
        # Start the painting interface
        print("Starting painting interface...")
        painter.start()
        
        # Test sequence: draw, then erase
        test_prompts = [
            "Draw a simple red circle in the center of the canvas",
            "Add some blue paint strokes around the circle", 
            "Use the eraser to remove parts of the blue strokes",
            "Use the eraser to clean up the edges of the red circle"
        ]
        
        print("\n=== Testing Eraser Functionality ===")
        
        # Execute the test sequence
        actions = painter.paint_sequence(test_prompts)
        
        # Display results
        print("\n=== Test Results ===")
        for i, action in enumerate(actions):
            print(f"Action {i+1}: {action.brush} brush - {action.reasoning}")
            if action.brush == "eraser":
                print(f"  ✓ Eraser action executed successfully!")
        
        # Save the final result
        painter.bridge.capture_canvas("eraser_test_result.png")
        print(f"\nTest completed! Result saved as 'eraser_test_result.png'")
        
        # Wait for user to see the result
        input("Press Enter to close the browser...")
        
    except Exception as e:
        print(f"Error during test: {e}")
    
    finally:
        painter.close()

if __name__ == "__main__":
    test_eraser_functionality() 