#!/usr/bin/env python3
"""
Test script for drawing_canvas_bridge.py
Tests the bridge with random JSON drawing instructions matching the format from free_drawing_agent.py
"""

import json
import os
import random
import time
from drawing_canvas_bridge import DrawingCanvasBridge
from free_drawing_agent import DrawingInstruction

def generate_random_drawing_instruction():
    """Generate a random drawing instruction matching the JSON format"""
    
    # Available brushes and colors
    brushes = ["pen", "marker", "crayon", "wiggle", "spray", "fountain"]
    colors = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#000000"]
    
    # Generate random thinking text
    thinking_options = [
        "I'll draw a simple circle in the center of the canvas using a smooth curved stroke.",
        "Let me add a zigzag line across the canvas to create some dynamic movement.",
        "I'll create a spiral pattern starting from the top-left corner.",
        "Drawing some random dots scattered across the canvas for texture.",
        "Let me add a wavy line that flows from left to right across the canvas."
    ]
    
    # Generate random strokes (1-3 strokes per instruction)
    num_strokes = random.randint(1, 3)
    strokes = []
    
    for _ in range(num_strokes):
        # Generate a stroke with 3-8 points
        num_points = random.randint(3, 8)
        x_coords = []
        y_coords = []
        
        # Create a path across the 850x500 canvas (matching the p5.js canvas size)
        for i in range(num_points):
            x = random.randint(50, 800)  # Keep some margin from 850 width
            y = random.randint(50, 450)  # Keep some margin from 500 height
            x_coords.append(x)
            y_coords.append(y)
        
        strokes.append({
            "x": x_coords,
            "y": y_coords
        })
    
    # Create the instruction JSON
    instruction_data = {
        "thinking": random.choice(thinking_options),
        "brush": random.choice(brushes),
        "color": random.choice(colors),
        "strokes": strokes
    }
    
    return instruction_data

def create_drawing_instruction_from_json(json_data):
    """Convert JSON data to DrawingInstruction object"""
    instruction = DrawingInstruction(
        brush=json_data["brush"],
        color=json_data["color"],
        strokes=json_data["strokes"],
        thinking=json_data["thinking"]
    )
    return instruction

def test_drawing_bridge():
    """Test the drawing canvas bridge with random instructions"""
    
    print("🎨 Starting Drawing Canvas Bridge Test")
    print("=" * 50)
    
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Initialize the bridge
    bridge = DrawingCanvasBridge(enable_video_capture=True, capture_fps=10)
    
    try:
        # Start the canvas interface
        print("🖥️  Starting canvas interface...")
        bridge.start_canvas_interface()
        print("✅ Canvas interface started successfully!")
        
        # Clear canvas to start fresh
        print("\n🧹 Clearing canvas...")
        bridge.clear_canvas()
        
        # Start video capture
        print("🎥 Starting video capture...")
        bridge.start_video_capture("output/test_drawing_session.mp4")
        
        # Generate and execute 3 random drawing instructions
        num_tests = 3
        for i in range(num_tests):
            print(f"\n--- Test {i+1}/{num_tests} ---")
            
            # Generate random instruction
            json_data = generate_random_drawing_instruction()
            print(f"📋 Generated instruction JSON:")
            print(json.dumps(json_data, indent=2))
            
            # Convert to DrawingInstruction object
            instruction = create_drawing_instruction_from_json(json_data)
            print(f"✅ Created DrawingInstruction object:")
            print(f"   Brush: {instruction.brush}")
            print(f"   Color: {instruction.color}")
            print(f"   Thinking: {instruction.thinking}")
            print(f"   Strokes: {len(instruction.strokes)} stroke(s)")
            
            # Execute the instruction
            print(f"🎯 Executing instruction...")
            bridge.execute_instruction(instruction, step_number=i+1)
            
            # Capture the result
            output_filename = f"test_result_step_{i+1}.png"
            bridge.capture_canvas(output_filename)
            print(f"📸 Canvas captured as: {output_filename}")
            
            # Wait longer between instructions to see the drawing
            print(f"⏳ Waiting 5 seconds before next instruction...")
            time.sleep(5)
        
        # Stop video capture
        print("\n🎬 Stopping video capture...")
        bridge.stop_video_capture()
        
        # Final capture
        print("📸 Capturing final result...")
        bridge.capture_canvas("test_final_result.png")
        
        print("\n🎉 Test completed successfully!")
        print("Files generated:")
        print("  - test_drawing_session.mp4 (video)")
        print("  - test_result_step_1.png")
        print("  - test_result_step_2.png") 
        print("  - test_result_step_3.png")
        print("  - test_final_result.png")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        bridge.close()
        print("✅ Test cleanup completed")

def test_json_format():
    """Test just the JSON generation without the canvas"""
    print("🧪 Testing JSON format generation...")
    
    for i in range(3):
        print(f"\n--- Sample JSON {i+1} ---")
        json_data = generate_random_drawing_instruction()
        print(json.dumps(json_data, indent=2))
        
        # Validate the structure
        required_fields = ["thinking", "brush", "color", "strokes"]
        for field in required_fields:
            if field not in json_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Validate strokes structure
        for stroke in json_data["strokes"]:
            if "x" not in stroke or "y" not in stroke:
                print(f"❌ Invalid stroke structure")
                return False
            if len(stroke["x"]) != len(stroke["y"]):
                print(f"❌ Mismatched x/y coordinate lengths")
                return False
    
    print("✅ JSON format validation passed!")
    return True

if __name__ == "__main__":
    print("Drawing Canvas Bridge Test Script")
    print("=================================")
    
    # First test JSON generation
    if test_json_format():
        print("\n" + "="*50)
        
        # Ask user if they want to run the full canvas test
        try:
            response = input("Run full canvas test? (y/n): ").lower().strip()
            if response == 'y' or response == 'yes':
                test_drawing_bridge()
            else:
                print("Skipping full canvas test. JSON format test completed successfully!")
        except KeyboardInterrupt:
            print("\n⚠️  Test interrupted by user")
        except Exception as e:
            print(f"❌ Unexpected error: {e}") 