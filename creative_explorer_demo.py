#!/usr/bin/env python3
"""
Creative Explorer Demo script for the Drawing Agent system.
This script demonstrates how the LLM-powered drawing agent
can make creative decisions at multiple stages and explore the canvas freely.
"""

import os
import sys
from dotenv import load_dotenv
from painting_bridge import AutomatedPainter

# Load environment variables from .env file
load_dotenv()

def main():
    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Get the path to the painter.html file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    painter_url = f"file://{current_dir}/painter.html"
    
    # Initialize the automated painter
    painter = AutomatedPainter(api_key=api_key, painter_url=painter_url)
    
    try:
        print("🎨 Starting Creative Explorer Demo")
        print("=" * 50)
        
        # Start the painting interface
        painter.start()
        
        # Capture initial blank canvas
        painter.bridge.capture_canvas("stage_0.png")
        
        # Stage 1: Initial creative decision
        print("\n🤔 Stage 1: Agent decides what to create...")
        initial_prompt = "You are an autonomous artist with a blank canvas. What would you like to create today? Think about something creative and interesting that you'd enjoy drawing. Describe your artistic vision and what elements you'd like to include in your artwork."
        animal_prompt = "You are an autonomous artist with a blank canvas. What would you like to create today? Think about an animal that you'd like to draw."
        initial_action = painter.agent.analyze_and_plan(animal_prompt, "stage_0.png")
        initial_vision = initial_action.reasoning
        print(f"🎯 Agent's initial vision: {initial_vision}")
        
        # Execute the initial action
        painter.bridge.execute_action(initial_action)
        painter.bridge.capture_canvas("stage_1.png")
        
        # Stage 2: Agent decides what to add next
        print("\n🎨 Stage 2: Agent decides what to add next...")
        next_prompt = f"Looking at your current artwork, what would you like to add next? Consider what would enhance your {initial_vision.lower()} creation. Think about composition, balance, and artistic flow."
        
        next_action = painter.agent.analyze_and_plan(next_prompt, "stage_1.png")
        next_decision = next_action.reasoning
        print(f"🎯 Agent's next decision: {next_decision}")
        
        # Execute the next action
        painter.bridge.execute_action(next_action)
        painter.bridge.capture_canvas("stage_2.png")
        
        # Stage 3: Agent explores new areas
        print("\n🌟 Stage 3: Agent explores new areas...")
        explore_prompt = f"Now explore different areas of the canvas. What new elements or details would you like to add to your {initial_vision.lower()} artwork? Consider experimenting with different techniques and areas of the canvas."
        
        explore_action = painter.agent.analyze_and_plan(explore_prompt, "stage_2.png")
        explore_decision = explore_action.reasoning
        print(f"🎯 Agent's exploration: {explore_decision}")
        
        # Execute the exploration action
        painter.bridge.execute_action(explore_action)
        painter.bridge.capture_canvas("stage_3.png")
        
        # Stage 4: Agent refines and enhances
        print("\n✨ Stage 4: Agent refines and enhances...")
        refine_prompt = f"Look at your artwork so far. What final touches or refinements would you like to add to complete your {initial_vision.lower()} masterpiece? Consider details, balance, and artistic polish."
        
        refine_action = painter.agent.analyze_and_plan(refine_prompt, "stage_3.png")
        refine_decision = refine_action.reasoning
        print(f"🎯 Agent's refinements: {refine_decision}")
        
        # Execute the refinement action
        painter.bridge.execute_action(refine_action)
        painter.bridge.capture_canvas("stage_4.png")
        
        # Stage 5: Final creative flourish
        print("\n🎭 Stage 5: Final creative flourish...")
        final_prompt = f"Give your {initial_vision.lower()} artwork a final creative flourish. What special touch or artistic element would make this piece truly unique and complete?"
        
        final_action = painter.agent.analyze_and_plan(final_prompt, "stage_4.png")
        final_decision = final_action.reasoning
        print(f"🎯 Agent's final flourish: {final_decision}")
        
        # Execute the final action
        painter.bridge.execute_action(final_action)
        
        # Save the final result
        output_filename = f"creative_explorer_final.png"
        painter.bridge.capture_canvas(output_filename)
        print(f"✅ Creative explorer artwork completed! Saved as '{output_filename}'")
        
        print("\n🎉 Creative Explorer demo completed successfully!")
        print(f"Generated file: {output_filename}")
        print("\n📋 Creative Journey Summary:")
        print(f"  Stage 1: {initial_vision}")
        print(f"  Stage 2: {next_decision}")
        print(f"  Stage 3: {explore_decision}")
        print(f"  Stage 4: {refine_decision}")
        print(f"  Stage 5: {final_decision}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        painter.close()
        print("\n👋 Creative Explorer demo finished. Browser closed.")

if __name__ == "__main__":
    main() 