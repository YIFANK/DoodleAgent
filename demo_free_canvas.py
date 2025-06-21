#!/usr/bin/env python3
"""
Demo script for Free Drawing Agent with drawing_canvas.html
This demonstrates an AI agent that freely creates art on a canvas,
deciding what to draw based on the current state of the canvas.
"""

import os
import sys
from dotenv import load_dotenv
from drawing_canvas_bridge import AutomatedDrawingCanvas

# Load environment variables from .env file
load_dotenv()

def main():
    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Get the path to the drawing_canvas.html file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    canvas_url = f"file://{current_dir}/drawing_canvas.html"
    
    # Initialize the automated drawing canvas
    canvas = AutomatedDrawingCanvas(api_key=api_key, canvas_url=canvas_url)
    
    try:
        print("🎨 Starting Free Drawing Canvas Demo")
        print("=" * 50)
        print("🤖 The AI artist will analyze the canvas and freely decide what to draw!")
        print("   Watch as it creates original artwork step by step.")
        print("=" * 50)
        
        # Start the canvas interface
        canvas.start()
        
        print("\n🖼️ Canvas is ready! The AI artist is now analyzing the blank canvas...")
        
        # Let the user choose between different demo modes
        print("\nChoose a demo mode:")
        print("1. Quick Demo (3 drawing steps)")
        print("2. Extended Demo (7 drawing steps)")
        print("3. Custom Demo (specify number of steps)")
        print("4. Interactive Demo (you ask questions)")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            # Quick demo
            print("\n🎯 Running Quick Demo...")
            canvas.creative_session(num_iterations=3)
            
        elif choice == "2":
            # Extended demo
            print("\n🎯 Running Extended Demo...")
            canvas.creative_session(num_iterations=7)
            
        elif choice == "3":
            # Custom demo
            try:
                num_steps = int(input("Enter number of drawing steps: "))
                if num_steps > 0:
                    print(f"\n🎯 Running Custom Demo with {num_steps} steps...")
                    canvas.creative_session(num_iterations=num_steps)
                else:
                    print("Invalid number of steps, running quick demo instead...")
                    canvas.creative_session(num_iterations=3)
            except ValueError:
                print("Invalid input, running quick demo instead...")
                canvas.creative_session(num_iterations=3)
                
        elif choice == "4":
            # Interactive demo
            print("\n🎯 Running Interactive Demo...")
            print("You can ask the AI what to draw next. Type 'quit' to stop.")
            
            # Create output directory
            os.makedirs("output", exist_ok=True)
            
            step = 0
            while True:
                step += 1
                print(f"\n--- Interactive Step {step} ---")
                
                # Get user question
                question = input("What would you like to ask the AI to draw? (or 'quit'): ").strip()
                if question.lower() in ['quit', 'exit', 'stop']:
                    break
                
                if not question:
                    question = "What would you like to draw next?"
                
                # Execute drawing step
                canvas_file = f"output/interactive_step_{step}.png"
                instruction = canvas.draw_from_canvas(canvas_file, question)
                
                print(f"🎨 AI's response: {instruction.reasoning}")
                print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")
                
                # Show strokes summary
                print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                for i, stroke in enumerate(instruction.strokes):
                    print(f"   {i+1}. {stroke['description']}")
            
            # Save final interactive artwork
            canvas.bridge.capture_canvas("output/interactive_final.png")
            print(f"\n🎉 Interactive session completed!")
            print(f"Final artwork saved as: output/interactive_final.png")
        
        else:
            print("Invalid choice, running quick demo...")
            canvas.creative_session(num_iterations=3)
        
        print(f"\n🎉 Demo completed successfully!")
        print("Check the 'output' folder for saved artwork images.")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        canvas.close()
        print("\n👋 Demo finished. Browser closed.")

def test_agent_only():
    """Test just the agent without the browser interface"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return
    
    from free_drawing_agent import FreeDrawingAgent
    import json
    
    agent = FreeDrawingAgent(api_key=api_key)
    
    # Test with the existing canvas image if available
    canvas_path = "current_canvas.png"
    if os.path.exists(canvas_path):
        print("🧪 Testing agent with existing canvas image...")
        instruction = agent.create_drawing_instruction(
            canvas_path, 
            "Looking at this canvas, what creative element would you add?"
        )
        
        print("Generated Drawing Instruction:")
        print(json.dumps({
            "brush": instruction.brush,
            "color": instruction.color,
            "strokes": instruction.strokes,
            "reasoning": instruction.reasoning
        }, indent=2))
    else:
        print(f"Canvas image not found: {canvas_path}")
        print("To test the agent, place a canvas image at 'current_canvas.png'")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-agent":
        test_agent_only()
    else:
        main() 