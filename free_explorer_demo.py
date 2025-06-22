#!/usr/bin/env python3
"""
Free Explorer Demo script for the Drawing Agent system.
This script gives the agent complete freedom to explore the canvas
and make all artistic decisions autonomously.
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
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # Get the path to the painter.html file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    painter_url = f"file://{current_dir}/allbrush.html"
    
    # Initialize the automated painter
    painter = AutomatedPainter(api_key=api_key, painter_url=painter_url)
    
    try:
        print("🎨 Starting Free Explorer Demo")
        print("=" * 50)
        print("🤖 The agent has complete artistic freedom!")
        print("   It will decide what to create, how to create it,")
        print("   and when it's satisfied with the result.")
        print("=" * 50)
        
        # Start the painting interface
        painter.start()
        
        # Capture initial blank canvas
        painter.bridge.capture_canvas(os.path.join(output_dir, "free_stage_0.png"))
        
        # Initial creative freedom
        print("\n🤔 Agent is contemplating the blank canvas...")
        initial_prompt = """You are a creative, autonomous artist. You create artworks no ones has ever seen before to express yourself. Your task is to use various brushes to scribble according to the current canvas state, then providing specific drawing strokes using simple stroke creation."""
        # Ask the LLM to generate a color palette
        palette_prompt = """As an artist, generate a harmonious color palette of 5-7 colors that would work well together in an abstract artwork. 
        Provide the colors in hex format (#RRGGBB) separated by commas."""
        
        palette_response = painter.agent.client.messages.create(
            model=painter.agent.model,
            max_tokens=6000,
            temperature=1,
            messages=[{"role": "user", "content": palette_prompt}]
        )
        
        # Extract hex colors from response using simple parsing
        palette_text = palette_response.content[0].text
        palette = [c.strip() for c in palette_text.split(',') if '#' in c]
        
        print("\n🎨 Generated color palette:")
        for color in palette:
            print(f"  {color}")
        initial_action = painter.agent.analyze_and_plan(initial_prompt, os.path.join(output_dir, "free_stage_0.png"))
        initial_vision = initial_action.reasoning
        print(f"🎯 Agent's creative vision: {initial_vision}")
        
        # Execute the initial action
        painter.bridge.execute_action(initial_action)
        painter.bridge.capture_canvas(os.path.join(output_dir, "free_stage_1.png"))
        
        # Free exploration loop - agent decides everything
        stage_count = 1
        max_stages = 200  # Safety limit
        creative_journey = [initial_vision]
        
        while stage_count < max_stages:
            stage_count += 1
            current_stage_file = os.path.join(output_dir, f"free_stage_{stage_count-1}.png")
            
            print(f"\n🎨 Free Stage {stage_count}: Agent explores freely...")
            
            # Give the agent complete freedom to decide what to do
            free_prompt = f"""You are a creative, autonomous artist. You create artworks no ones has ever seen before to express yourself. Your task is to use various brushes to scribble according to the current canvas state, then providing specific drawing strokes using simple stroke creation.

You are working on your artwork. Look at what you've created so far and decide:

1. What would you like to do next? (add, modify, explore, experiment, etc.)
2. Are you satisfied with your creation, or do you want to continue?

IMPORTANT: 
1. You must ONLY use colors from the provided color palette: {', '.join(palette)}
2. At the end of your response, clearly state your decision:
   - If you want to CONTINUE: End with "DECISION: CONTINUE"
   - If you want to FINISH: End with "DECISION: FINISH"

Be bold, be creative, be free, be expressive, be yourself. Fill the whole canvas with your art.

USE a variety of brushes to create a variety of effects. Do not leave the canvas blank."""
            
            free_action = painter.agent.analyze_and_plan(free_prompt, current_stage_file)
            free_decision = free_action.reasoning
            creative_journey.append(free_decision)
            print(f"🎯 Agent's free choice: {free_decision}")
            
            # Check the agent's explicit decision
            wants_to_finish = "DECISION: FINISH" in free_decision.upper()
            
            if wants_to_finish:
                print(f"🎭 Agent explicitly decided to finish!")
                # Execute the final action
                painter.bridge.execute_action(free_action)
                break
            else:
                print(f"🔄 Agent wants to continue exploring...")
                # Execute the action and continue
                painter.bridge.execute_action(free_action)
                print("Agent has executed the action:", free_action)
                painter.bridge.capture_canvas(os.path.join(output_dir, f"free_stage_{stage_count}.png"))
        
        # If we reached max stages, give one final opportunity
        if stage_count >= max_stages:
            print(f"\n⏰ Maximum exploration time reached. One final artistic choice...")
            final_prompt = f"""You've been exploring your artwork for {stage_count} stages. 

What final artistic choice would you like to make? 
This is your last opportunity to add, modify, or complete your creation.

End your response with "DECISION: FINISH" since this is the final stage."""
            
            final_action = painter.agent.analyze_and_plan(final_prompt, os.path.join(output_dir, f"free_stage_{stage_count}.png"))
            final_decision = final_action.reasoning
            creative_journey.append(f"Final choice: {final_decision}")
            print(f"🎯 Final artistic choice: {final_decision}")
            
            painter.bridge.execute_action(final_action)
        
        # Save the final result
        output_filename = os.path.join(output_dir, "free_explorer_masterpiece.png")
        painter.bridge.capture_canvas(output_filename)
        print(f"✅ Free explorer masterpiece completed! Saved as '{output_filename}'")
        
        print(f"\n🎉 Free Explorer demo completed successfully!")
        print(f"Generated file: {output_filename}")
        print(f"Total creative stages: {stage_count}")
        print(f"\n📋 Creative Journey:")
        for i, decision in enumerate(creative_journey):
            print(f"  Stage {i+1}: {decision}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        painter.close()
        print("\n👋 Free Explorer demo finished. Browser closed.")

if __name__ == "__main__":
    main() 