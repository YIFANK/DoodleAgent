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

        # Create timestamped output directory for this run
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_output_dir = f"output/{timestamp}"
        os.makedirs(run_output_dir, exist_ok=True)
        print(f"📁 Created output directory: {run_output_dir}")

        # Let the user choose between different demo modes
        print("\nChoose a demo mode:")
        print("1. Quick Demo (3 drawing steps)")
        print("2. Extended Demo (7 drawing steps)")
        print("3. Custom Demo (specify number of steps)")
        print("4. Interactive Demo (you ask questions)")
        print("5. Mood-Based Demo (express artistic moods through drawing)")
        print("6. Abstract Demo (create non-representational art)")

        choice = input("\nEnter your choice (1-6): ").strip()

        if choice == "1":
            # Quick demo
            print("\n🎯 Running Quick Demo...")
            canvas.creative_session(num_iterations=3, output_dir=run_output_dir)

        elif choice == "2":
            # Extended demo
            print("\n🎯 Running Extended Demo...")
            canvas.creative_session(num_iterations=7, output_dir=run_output_dir)

        elif choice == "3":
            # Custom demo
            try:
                num_steps = int(input("Enter number of drawing steps: "))
                if num_steps > 0:
                    print(f"\n🎯 Running Custom Demo with {num_steps} steps...")
                    canvas.creative_session(num_iterations=num_steps, output_dir=run_output_dir)
                else:
                    print("Invalid number of steps, running quick demo instead...")
                    canvas.creative_session(num_iterations=3, output_dir=run_output_dir)
            except ValueError:
                print("Invalid input, running quick demo instead...")
                canvas.creative_session(num_iterations=3, output_dir=run_output_dir)

        elif choice == "4":
            # Interactive demo
            print("\n🎯 Running Interactive Demo...")
            print("You can ask the AI what to draw next. Type 'quit' to stop.")

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
                canvas_file = f"{run_output_dir}/interactive_step_{step}.png"
                instruction = canvas.draw_from_canvas(canvas_file, question)

                print(f"🎨 AI's response: {instruction.reasoning}")
                print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                # Show strokes summary
                print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                for i, stroke in enumerate(instruction.strokes):
                    print(f"   {i+1}. {stroke['description']}")

            # Save final interactive artwork
            canvas.bridge.capture_canvas(f"{run_output_dir}/interactive_final.png")
            print(f"\n🎉 Interactive session completed!")
            print(f"Final artwork saved as: {run_output_dir}/interactive_final.png")

        elif choice == "5":
            # Mood-based demo
            print("\n🎯 Running Mood-Based Demo...")
            print("The AI will autonomously determine artistic moods and create drawings that express them!")
            print("Each step starts with the AI choosing a mood, then creating art that embodies that mood.")

            # Run for 30 automatic iterations
            num_iterations = 30
            for step in range(1, num_iterations + 1):
                print(f"\n--- Mood Step {step} ---")
                print(f"🎨 AI is determining the mood for this step...")

                # Execute mood-based drawing step (LLM determines mood autonomously)
                canvas_file = f"{run_output_dir}/mood_step_{step}.png"
                instruction = canvas.draw_from_emotion(canvas_file)  # No mood parameter - LLM chooses

                print(f"🎨 AI's mood: {instruction.reasoning}")
                print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                # Show strokes summary
                print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                for i, stroke in enumerate(instruction.strokes):
                    print(f"   {i+1}. {stroke['description']}")

            # Save final mood-based artwork
            canvas.bridge.capture_canvas(f"{run_output_dir}/mood_final.png")
            print(f"\n🎉 Mood-based session completed!")
            print(f"Final artwork saved as: {run_output_dir}/mood_final.png")

        elif choice == "6":
            # Abstract demo
            print("\n🎯 Running Abstract Demo...")
            print("The AI will create pure, non-representational art!")
            print("No concrete objects - just abstract shapes, lines, and pure creativity.")

            num_iterations = 30
            for step in range(1, num_iterations + 1):
                print(f"\n--- Abstract Step {step} ---")
                print(f"🎨 AI is creating abstract art...")

                # Execute abstract drawing step
                canvas_file = f"{run_output_dir}/abstract_step_{step}.png"
                instruction = canvas.draw_from_abstract(canvas_file)

                print(f"🎨 AI's abstract creation: {instruction.reasoning}")
                print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                # Show strokes summary
                print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                for i, stroke in enumerate(instruction.strokes):
                    print(f"   {i+1}. {stroke['description']}")

            # Save final abstract artwork
            canvas.bridge.capture_canvas(f"{run_output_dir}/abstract_final.png")
            print(f"\n🎉 Abstract session completed!")
            print(f"Final artwork saved as: {run_output_dir}/abstract_final.png")

        else:
            print("Invalid choice, running quick demo...")
            canvas.creative_session(num_iterations=3, output_dir=run_output_dir)

        print(f"\n🎉 Demo completed successfully!")
        print(f"Check the '{run_output_dir}' folder for saved artwork images.")

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
