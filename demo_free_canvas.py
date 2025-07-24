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
import random
import math
from free_drawing_agent import DrawingInstruction
# Load environment variables from .env file
load_dotenv()

def main():
    # Check if API key is provided
    claude_api_key = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not claude_api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        sys.exit(1)

    # Get the path to the drawing_canvas.html file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    canvas_url = f"file://{current_dir}/drawing_canvas.html"

    # Initialize the automated drawing canvas with video capture enabled
    canvas = AutomatedDrawingCanvas(api_key=claude_api_key, canvas_url=canvas_url, enable_video_capture=True, capture_fps=30,model_type="claude")

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
            finally:
                # Stop video capture
                canvas.bridge.stop_video_capture()
                #save the final canvas image to ../output/free_canvas/timestamp.png
                canvas.bridge.capture_canvas(f"../output/free_canvas/{timestamp}.png")

        elif choice == "4":
            # Interactive demo
            print("\n🎯 Running Interactive Demo...")
            print("You can ask the AI what to draw next. Type 'quit' to stop.")
            print("🎥 Video recording enabled - capturing the entire interactive session!")

            # Start video capture for interactive session
            video_output = f"{run_output_dir}/interactive_session_{timestamp}.mp4"
            canvas.bridge.start_video_capture(video_output)

            step = 0
            try:
                # Get initial question that will guide the entire drawing session
                question = input("What would you like the AI to draw? (or 'quit'): ").strip()
                if question.lower() in ['quit', 'exit', 'stop']:
                    return
                
                if not question:
                    question = "Create an abstract artistic composition"
                max_steps = 15
                while step < max_steps:
                    step += 1
                    print(f"\n--- Interactive Step {step} ---")

                    # Execute drawing step
                    canvas_file = f"{run_output_dir}/interactive_step_{step}.png"
                    instruction = canvas.draw_from_canvas(canvas_file, question, step_number=step)

                    print(f"🎨 AI's response: {instruction.thinking}")
                    print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                    # Show strokes summary
                    print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                    for i, stroke in enumerate(instruction.strokes):
                        print(f"   {i+1}. {stroke['x']}, {stroke['y']}")

                # Save final interactive artwork
                canvas.bridge.capture_canvas(f"{run_output_dir}/interactive_final.png")
                print(f"\n🎉 Interactive session completed!")
                print(f"Final artwork saved as: {run_output_dir}/interactive_final.png")
                print(f"🎬 Video saved as: {video_output}")
                
            finally:
                # Stop video capture
                canvas.bridge.stop_video_capture()
                #save the final canvas image to ../output/free_canvas/timestamp.png
                canvas.bridge.capture_canvas(f"../output/interactive/{timestamp}.png")

        elif choice == "5":
            # Mood-based demo
            print("\n🎯 Running Mood-Based Demo...")
            print("The AI will autonomously determine artistic moods and create drawings that express them!")
            print("Each step starts with the AI choosing a mood, then creating art that embodies that mood.")
            print("🎥 Video recording enabled - capturing the entire mood-based session!")

            # Start video capture for mood-based session
            video_output = f"{run_output_dir}/mood_session_{timestamp}.mp4"
            canvas.bridge.start_video_capture(video_output)

            # Run for 15 automatic iterations
            num_iterations = 15
            #get users input for the mood
            mood = input("Enter a mood for the AI to express: ")
            try:
                for step in range(1, num_iterations + 1):
                    print(f"\n--- Mood Step {step} ---")
                    print(f"🎨 AI is determining the mood for this step...")

                    # Execute mood-based drawing step (LLM determines mood autonomously)
                    canvas_file = f"{run_output_dir}/mood_step_{step}.png"
                    instruction = canvas.draw_from_emotion(canvas_file, emotion=mood, step_number=step)  # No mood parameter - LLM chooses

                    print(f"🎨 AI's mood: {instruction.thinking}")
                    print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                    # Show strokes summary
                    print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                    for i, stroke in enumerate(instruction.strokes):
                        print(f"   {i+1}. {stroke['x']}, {stroke['y']}")

                # Save final mood-based artwork
                canvas.bridge.capture_canvas(f"{run_output_dir}/mood_{mood}.png")
                print(f"\n🎉 Mood-based session completed!")
                print(f"Final artwork saved as: {run_output_dir}/mood_{mood}.png")
                print(f"🎬 Video saved as: {video_output}")
                
            finally:
                # Stop video capture
                canvas.bridge.stop_video_capture()
                #save the final canvas image to ../output/free_canvas/timestamp.png
                canvas.bridge.capture_canvas(f"../output/mood/{mood}_{timestamp}.png")
        elif choice == "6":
            # Abstract demo
            print("\n🎯 Running Abstract Demo...")
            print("The AI will create pure, non-representational art!")
            print("No concrete objects - just abstract shapes, lines, and pure creativity.")
            print("🎥 Video recording enabled - capturing the entire abstract session!")

            # Start video capture for abstract session
            video_output = f"{run_output_dir}/abstract_session_{timestamp}.mp4"
            canvas.bridge.start_video_capture(video_output)

            num_iterations = 30
            try:
                for step in range(1, num_iterations + 1):
                    print(f"\n--- Abstract Step {step} ---")
                    print(f"🎨 AI is creating abstract art...")

                    # Execute abstract drawing step
                    canvas_file = f"{run_output_dir}/abstract_step_{step}.png"
                    instruction = canvas.draw_from_abstract(canvas_file, step_number=step)

                    print(f"🎨 AI's abstract creation: {instruction.reasoning}")
                    print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                    # Show strokes summary
                    print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                    for i, stroke in enumerate(instruction.strokes):
                        print(f"   {i+1}. {stroke['x']}, {stroke['y']}")

                # Save final abstract artwork
                canvas.bridge.capture_canvas(f"{run_output_dir}/abstract_final.png")
                print(f"\n🎉 Abstract session completed!")
                print(f"Final artwork saved as: {run_output_dir}/abstract_final.png")
                print(f"🎬 Video saved as: {video_output}")
                
            finally:
                # Stop video capture
                canvas.bridge.stop_video_capture()
        elif choice == "7":
            #random strokes
            # print("\n🎯 Running Random Strokes Demo...")
            # print("The AI will create random strokes on the canvas.")
            # print("🎥 Video recording enabled - capturing the entire random strokes session!")

            # # Start video capture for random strokes session
            # video_output = f"{run_output_dir}/random_strokes_session_{timestamp}.mp4"
            # canvas.bridge.start_video_capture(video_output)
            num_iterations = 15
            try:
                for step in range(1, num_iterations + 1):
                    print(f"\n--- Random Stroke Step {step} ---")
                    
                    # Random stroke length between 3-7 points
                    stroke_length = random.randint(3, 7)
                    
                    # Random starting point
                    start_x = random.uniform(0, 850)  # Keep within canvas bounds
                    start_y = random.uniform(0, 500)
                    
                    # Generate points for the stroke
                    x_points = [start_x]
                    y_points = [start_y]
                    
                    # Circle radius for next point sampling
                    radius = 100
                    
                    # Generate subsequent points
                    for _ in range(stroke_length - 1):
                        # Get last point
                        last_x = x_points[-1]
                        last_y = y_points[-1]
                        
                        # Random angle and distance within circle
                        angle = random.uniform(0, 2 * math.pi)
                        distance = random.uniform(0, radius)
                        
                        # Calculate next point
                        #do random next point
                        # next_x = random.uniform(0,850)
                        # next_y = random.uniform(0,500)
                        next_x = last_x + distance * math.cos(angle)
                        next_y = last_y + distance * math.sin(angle)
                        
                        # # Keep within canvas bounds
                        next_x = max(0, min(850, next_x))
                        next_y = max(0, min(500, next_y))
                        
                        x_points.append(next_x)
                        y_points.append(next_y)
                    
                    # Random color from palette
                    color_family = random.choice(list(canvas.agent.color_palette.keys()))
                    color = random.choice(list(canvas.agent.color_palette[color_family].values()))
                    # Random brush
                    brush = random.choice(['marker', 'crayon', 'wiggle', 'spray', 'fountain'])
                    print(x_points,y_points)
                    # Create stroke data
                    stroke = {
                        'x': x_points,
                        'y': y_points,      
                    }
                    
                    # Execute the stroke
                    instruction = DrawingInstruction(
                        brush=brush,
                        color=color,
                        strokes=[stroke],
                        thinking=f"Random stroke with {brush} brush"
                    )
                    canvas.bridge.execute_instruction(instruction, step)
                    
                    print(f"🖌️ Drew {stroke_length}-point stroke with {brush} brush in {color}")
                
                # Save final random strokes artwork
                canvas.bridge.capture_canvas(f"{run_output_dir}/random_strokes_final.png")
                print(f"\n🎉 Random strokes session completed!")
                # print(f"Final artwork saved as: {run_output_dir}/random_strokes_final.png")
                # print(f"🎬 Video saved as: {video_output}")
                
            finally:
                # Stop video capture
                canvas.bridge.stop_video_capture()
        else:
            print("Invalid choice, running quick demo...")
            canvas.creative_session(num_iterations=3, output_dir=run_output_dir)

        print(f"\n🎉 Demo completed successfully!")
        print(f"Check the '{run_output_dir}' folder for saved artwork images.")

    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    # except Exception as e:
    #     print(f"\n❌ Error during demo: {e}")
    #     import traceback
    #     traceback.print_exc()

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
            "thinking": instruction.thinking
        }, indent=2))
    else:
        print(f"Canvas image not found: {canvas_path}")
        print("To test the agent, place a canvas image at 'current_canvas.png'")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test-agent":
        test_agent_only()
    else:
        main()
