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

    #ask user to choose a model
    print("Choose a model:")
    print("1. Claude")
    print("2. OpenAI")
    print("3. Gemini")
    model_choice = input("Enter your choice (1-3): ").strip()
    if model_choice == "1":
        model_type = "claude"
        api_key = claude_api_key
    elif model_choice == "2":
        model_type = "openai"
        api_key = openai_api_key
    elif model_choice == "3":
        model_type = "gemini"
        api_key = gemini_api_key
    else:
        print("Invalid choice, defaulting to Claude")
        model_type = "claude"
        api_key = claude_api_key

    # Get the path to the drawing_canvas.html file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    canvas_url = f"file://{current_dir}/drawing_canvas.html"

    # Initialize the automated drawing canvas with video capture enabled
    canvas = AutomatedDrawingCanvas(api_key=api_key, canvas_url=canvas_url, enable_video_capture=True, capture_fps=30, model_type=model_type, verbose=True)

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
        # print("4. Interactive Demo (you ask questions)") # Disabled for now
        print("5. Mood-Based Demo (express artistic moods through drawing)")
        print("6. Abstract Demo (create non-representational art)")
        print("7. Random Strokes Demo (random stroke generation)")

        choice = input("\nEnter your choice (1-3, 5-7): ").strip()

        # Ask for number of repetitions for all modes except interactive
        num_repeats = 1
        if choice != "4":  # Interactive mode doesn't need repeats (and is disabled)
            try:
                repeat_input = input("\nHow many times to repeat this run? (default: 1): ").strip()
                if repeat_input:
                    num_repeats = int(repeat_input)
                    if num_repeats <= 0:
                        num_repeats = 1
                        print("Invalid number, using default of 1 repeat")
            except ValueError:
                num_repeats = 1
                print("Invalid input, using default of 1 repeat")

        # Handle disabled interactive mode
        if choice == "4":
            print("Interactive demo is temporarily disabled. Please choose another option.")
            return

        # Initialize variables for custom demo
        num_steps = 3  # default value

        # Run the selected demo num_repeats times
        for repeat_run in range(num_repeats):
            if num_repeats > 1:
                print(f"\n{'='*60}")
                print(f"🔄 REPEAT RUN {repeat_run + 1}/{num_repeats}")
                print(f"{'='*60}")

                # Create new timestamped output directory for each repeat
                repeat_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                repeat_output_dir = f"output/{repeat_timestamp}"
                os.makedirs(repeat_output_dir, exist_ok=True)
                print(f"📁 Created output directory: {repeat_output_dir}")

                # Clear canvas for new run and ensure video capture is stopped
                if repeat_run > 0:
                    # Ensure any previous video capture is stopped
                    try:
                        canvas.bridge.stop_video_capture()
                    except:
                        pass  # Ignore if no video was running
                    # Small delay to ensure proper cleanup
                    import time
                    time.sleep(0.5)
                    canvas.bridge.clear_canvas()
            else:
                repeat_output_dir = run_output_dir

            if choice == "1":
                # Quick demo
                if repeat_run == 0:
                    print(f"\n🎯 Running Quick Demo {num_repeats} time(s)...")
                instructions = canvas.creative_session(num_iterations=3, output_dir=repeat_output_dir)
                
                # Save JSON logs
                session_name = f"quick_demo_repeat_{repeat_run + 1}"
                canvas.save_complete_session_data(repeat_output_dir, session_name, instructions)
                
                # Reset session for next repeat
                if repeat_run < num_repeats - 1:
                    canvas.agent.close_session_logs()
                    canvas.agent.reset_stroke_history()

            elif choice == "2":
                # Extended demo
                if repeat_run == 0:
                    print(f"\n🎯 Running Extended Demo {num_repeats} time(s)...")
                instructions = canvas.creative_session(num_iterations=7, output_dir=repeat_output_dir)
                
                # Save JSON logs
                session_name = f"extended_demo_repeat_{repeat_run + 1}"
                canvas.save_complete_session_data(repeat_output_dir, session_name, instructions)
                
                # Reset session for next repeat
                if repeat_run < num_repeats - 1:
                    canvas.agent.close_session_logs()
                    canvas.agent.reset_stroke_history()

            elif choice == "3":
                # Custom demo
                if repeat_run == 0:
                    try:
                        num_steps = int(input("Enter number of drawing steps: "))
                        if num_steps <= 0:
                            num_steps = 3
                            print("Invalid number of steps, using 3 instead...")
                    except ValueError:
                        num_steps = 3
                        print("Invalid input, using 3 steps instead...")

                    print(f"\n🎯 Running Custom Demo with {num_steps} steps, {num_repeats} time(s)...")

                # Setup video capture for custom demo
                repeat_ts = repeat_timestamp if num_repeats > 1 else timestamp
                custom_output_dir = f"../output/custom/{repeat_ts}"
                os.makedirs(custom_output_dir, exist_ok=True)
                
                print("🎥 Video recording enabled - capturing the entire custom session!")
                video_output = f"{custom_output_dir}/custom_session_{repeat_ts}_repeat_{repeat_run + 1}.mp4"
                
                # Ensure video capture is stopped before starting new one
                try:
                    canvas.bridge.stop_video_capture()
                except:
                    pass  # Ignore if no video was running
                    
                canvas.bridge.start_video_capture(video_output)

                try:
                    # Run the creative session and get the instructions
                    instructions = canvas.creative_session(num_iterations=num_steps, output_dir=repeat_output_dir)

                    # Save final canvas for custom demo
                    canvas.bridge.capture_canvas(f"{custom_output_dir}/{repeat_ts}.png")
                    
                    # Export session logs as JSON to the custom output directory
                    print("📝 Saving session logs as JSON...")
                    session_name = f"custom_demo_{repeat_ts}_repeat_{repeat_run + 1}"
                    canvas.save_complete_session_data(custom_output_dir, session_name, instructions)
                    
                    if repeat_run == num_repeats - 1:
                        print(f"\n🎉 Custom session completed!")
                        print(f"Final artwork saved as: {custom_output_dir}/{repeat_ts}.png")
                        print(f"🎬 Video saved as: {video_output}")

                finally:
                    # Stop video capture with error handling
                    try:
                        canvas.bridge.stop_video_capture()
                    except Exception as e:
                        print(f"Warning: Error stopping video capture: {e}")
                
                # Also close and reset the session for the next repeat
                if repeat_run < num_repeats - 1:
                    canvas.agent.close_session_logs()
                    canvas.agent.reset_stroke_history()

            elif choice == "5":
                # Mood-based demo
                if repeat_run == 0:
                    mood = input("Enter a mood for the AI to express: ").strip()
                    if not mood:
                        mood = "creative"
                    try:
                        num_iterations = int(input("How many strokes per run? (default: 15): ").strip() or "15")
                        if num_iterations <= 0:
                            num_iterations = 15
                    except ValueError:
                        num_iterations = 15
                        print("Invalid input, using 15 strokes per run")

                    print(f"\n🎯 Running Mood-Based Demo ({mood}) with {num_iterations} strokes, {num_repeats} time(s)...")

                # Setup standardized output directory for mood demo (same format as custom demo)
                repeat_ts = repeat_timestamp if num_repeats > 1 else timestamp
                mood_output_dir = f"../output/custom/{repeat_ts}"
                os.makedirs(mood_output_dir, exist_ok=True)

                print("🎥 Video recording enabled - capturing the entire mood-based session!")
                # Start video capture for mood-based session  
                video_output = f"{mood_output_dir}/mood_{mood}_{repeat_ts}_repeat_{repeat_run + 1}.mp4"
                
                # Ensure video capture is stopped before starting new one
                try:
                    canvas.bridge.stop_video_capture()
                except:
                    pass  # Ignore if no video was running
                    
                canvas.bridge.start_video_capture(video_output)

                # Collect instructions for JSON logging
                mood_instructions = []

                try:
                    for step in range(1, num_iterations + 1):
                        print(f"\n--- Mood Step {step} ---")
                        print(f"🎨 AI is determining the mood for this step...")

                        # Execute mood-based drawing step
                        canvas_file = f"{repeat_output_dir}/mood_step_{step}.png"
                        instruction = canvas.draw_from_emotion(canvas_file, emotion=mood, step_number=step)
                        
                        # Add to instructions list for JSON logging
                        mood_instructions.append(instruction)

                        print(f"🎨 AI's mood: {instruction.thinking}")
                        print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                        # Show strokes summary
                        print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                        for i, stroke in enumerate(instruction.strokes):
                            print(f"   {i+1}. {stroke['x']}, {stroke['y']}")

                    # Save final mood-based artwork to standardized directory
                    canvas.bridge.capture_canvas(f"{mood_output_dir}/mood_{mood}_{repeat_ts}.png")
                    
                    # Save JSON logs for mood-based session to standardized directory
                    print("📝 Saving mood-based session logs as JSON...")
                    session_name = f"mood_{mood}_{repeat_ts}_repeat_{repeat_run + 1}"
                    canvas.save_complete_session_data(mood_output_dir, session_name, mood_instructions)
                    
                    if repeat_run == num_repeats - 1:
                        print(f"\n🎉 Mood-based session completed!")
                        print(f"Final artwork saved as: {mood_output_dir}/mood_{mood}_{repeat_ts}.png")
                        print(f"🎬 Video saved as: {video_output}")

                finally:
                    # Stop video capture with error handling
                    try:
                        canvas.bridge.stop_video_capture()
                    except Exception as e:
                        print(f"Warning: Error stopping video capture: {e}")

                # Reset session for next repeat
                if repeat_run < num_repeats - 1:
                    canvas.agent.close_session_logs()
                    canvas.agent.reset_stroke_history()

            elif choice == "6":
                # Abstract demo
                if repeat_run == 0:
                    try:
                        num_iterations = int(input("How many strokes per run? (default: 30): ").strip() or "30")
                        if num_iterations <= 0:
                            num_iterations = 30
                    except ValueError:
                        num_iterations = 30
                        print("Invalid input, using 30 strokes per run")

                    print(f"\n🎯 Running Abstract Demo with {num_iterations} strokes, {num_repeats} time(s)...")

                print("🎥 Video recording enabled - capturing the entire abstract session!")
                # Get current timestamp for this repeat run
                current_ts = repeat_timestamp if num_repeats > 1 else timestamp
                # Start video capture for abstract session
                video_output = f"{repeat_output_dir}/abstract_session_{current_ts}_repeat_{repeat_run + 1}.mp4"
                
                # Ensure video capture is stopped before starting new one
                try:
                    canvas.bridge.stop_video_capture()
                except:
                    pass  # Ignore if no video was running
                    
                canvas.bridge.start_video_capture(video_output)

                # Collect instructions for JSON logging
                abstract_instructions = []

                try:
                    for step in range(1, num_iterations + 1):
                        print(f"\n--- Abstract Step {step} ---")
                        print(f"🎨 AI is creating abstract art...")

                        # Execute abstract drawing step
                        canvas_file = f"{repeat_output_dir}/abstract_step_{step}.png"
                        instruction = canvas.draw_from_abstract(canvas_file, step_number=step)
                        
                        # Add to instructions list for JSON logging
                        abstract_instructions.append(instruction)

                        print(f"🎨 AI's abstract creation: {instruction.reasoning}")
                        print(f"🖌️ Using {instruction.brush} brush with color {instruction.color}")

                        # Show strokes summary
                        print(f"📝 Drawing {len(instruction.strokes)} stroke(s):")
                        for i, stroke in enumerate(instruction.strokes):
                            print(f"   {i+1}. {stroke['x']}, {stroke['y']}")

                    # Save final abstract artwork
                    canvas.bridge.capture_canvas(f"{repeat_output_dir}/abstract_final.png")
                    
                    # Save JSON logs for abstract session
                    print("📝 Saving abstract session logs as JSON...")
                    session_name = f"abstract_{current_ts}_repeat_{repeat_run + 1}"
                    canvas.save_complete_session_data(repeat_output_dir, session_name, abstract_instructions)
                    
                    if repeat_run == num_repeats - 1:
                        print(f"\n🎉 Abstract session completed!")
                        print(f"Final artwork saved as: {repeat_output_dir}/abstract_final.png")
                        print(f"🎬 Video saved as: {video_output}")

                finally:
                    # Stop video capture with error handling
                    try:
                        canvas.bridge.stop_video_capture()
                    except Exception as e:
                        print(f"Warning: Error stopping video capture: {e}")

                # Reset session for next repeat
                if repeat_run < num_repeats - 1:
                    canvas.agent.close_session_logs()
                    canvas.agent.reset_stroke_history()

            elif choice == "7":
                # Random strokes demo
                if repeat_run == 0:
                    try:
                        num_iterations = int(input("How many strokes per run? (default: 15): ").strip() or "15")
                        if num_iterations <= 0:
                            num_iterations = 15
                    except ValueError:
                        num_iterations = 15
                        print("Invalid input, using 15 strokes per run")

                    print(f"\n🎯 Running Random Strokes Demo with {num_iterations} strokes, {num_repeats} time(s)...")

                # Get current timestamp for this repeat run
                current_ts = repeat_timestamp if num_repeats > 1 else timestamp
                # Start video capture for random strokes session
                video_output = f"{repeat_output_dir}/random_strokes_{current_ts}_repeat_{repeat_run + 1}.mp4"
                
                # Ensure video capture is stopped before starting new one
                try:
                    canvas.bridge.stop_video_capture()
                except:
                    pass  # Ignore if no video was running
                    
                canvas.bridge.start_video_capture(video_output)

                # Collect instructions for JSON logging
                random_instructions = []

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
                            next_x = last_x + distance * math.cos(angle)
                            next_y = last_y + distance * math.sin(angle)

                            # Keep within canvas bounds
                            next_x = max(0, min(850, next_x))
                            next_y = max(0, min(500, next_y))

                            x_points.append(next_x)
                            y_points.append(next_y)

                        # Random color from palette
                        color_family = random.choice(list(canvas.agent.color_palette.keys()))
                        color = random.choice(list(canvas.agent.color_palette[color_family].values()))
                        # Random brush
                        brush = random.choice(['marker', 'crayon', 'wiggle', 'spray', 'fountain'])
                        print(x_points, y_points)

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
                        
                        # Add to instructions list for JSON logging
                        random_instructions.append(instruction)

                        print(f"🖌️ Drew {stroke_length}-point stroke with {brush} brush in {color}")

                    # Save final random strokes artwork
                    canvas.bridge.capture_canvas(f"{repeat_output_dir}/random_strokes_final.png")
                    
                    # Save JSON logs for random strokes session
                    print("📝 Saving random strokes session logs as JSON...")
                    session_name = f"random_strokes_{current_ts}_repeat_{repeat_run + 1}"
                    canvas.save_complete_session_data(repeat_output_dir, session_name, random_instructions)
                    
                    if repeat_run == num_repeats - 1:
                        print(f"\n🎉 Random strokes session completed!")
                        print(f"🎬 Video saved as: {video_output}")

                finally:
                    # Stop video capture with error handling
                    try:
                        canvas.bridge.stop_video_capture()
                    except Exception as e:
                        print(f"Warning: Error stopping video capture: {e}")

                # Reset session for next repeat
                if repeat_run < num_repeats - 1:
                    canvas.agent.close_session_logs()
                    canvas.agent.reset_stroke_history()

            else:
                print("Invalid choice, running quick demo...")
                canvas.creative_session(num_iterations=3, output_dir=repeat_output_dir)

        print(f"\n🎉 Demo completed successfully!")
        print(f"Check the '{run_output_dir}' folder for saved artwork images and JSON logs.")

    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Ensure video capture is stopped before closing
        try:
            canvas.bridge.stop_video_capture()
        except:
            pass  # Ignore if no video was running
        
        # Ensure final session is properly closed
        try:
            canvas.agent.close_session_logs()
        except:
            pass  # Ignore if already closed
            
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
