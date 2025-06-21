#!/usr/bin/env python3
"""
Autonomous Explorer Demo script for the Drawing Agent system.
This script demonstrates how the LLM-powered drawing agent
can autonomously decide when to move to the next stage of creation.
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
        print("🎨 Starting Autonomous Explorer Demo")
        print("=" * 50)
        
        # Start the painting interface
        painter.start()
        
        # Capture initial blank canvas
        painter.bridge.capture_canvas("stage_0.png")
        
        # Stage 1: Initial creative decision
        print("\n🤔 Stage 1: Agent decides what to create...")
        initial_prompt = "You are an autonomous artist with a blank canvas. What would you like to create today? Think about something creative and interesting that you'd enjoy drawing. Describe your artistic vision and what elements you'd like to include in your artwork."
        
        initial_action = painter.agent.analyze_and_plan(initial_prompt, "stage_0.png")
        initial_vision = initial_action.reasoning
        print(f"🎯 Agent's initial vision: {initial_vision}")
        
        # Execute the initial action
        painter.bridge.execute_action(initial_action)
        painter.bridge.capture_canvas("stage_1.png")
        
        # Autonomous stages - let the agent decide when to move forward
        stage_count = 1
        max_stages = 8  # Safety limit to prevent infinite loops
        
        while stage_count < max_stages:
            stage_count += 1
            current_stage_file = f"stage_{stage_count-1}.png"
            
            print(f"\n🎨 Stage {stage_count}: Agent assesses progress and decides next action...")
            
            # Let the agent decide what to do next and whether to continue
            assessment_prompt = f"""You are an autonomous artist working on your {initial_vision.lower()} artwork. 

Look at your current progress and decide:
1. What would you like to add or modify next?
2. Are you satisfied with the current state of your artwork, or do you want to continue working on it?

Consider:
- What elements are missing or need improvement?
- How does the composition feel?
- What would enhance the overall artistic vision?
- Are you ready to finish, or do you need more work?

IMPORTANT: At the end of your response, clearly state your decision:
- If you want to CONTINUE: End with "DECISION: CONTINUE"
- If you want to FINISH: End with "DECISION: FINISH"

Respond with your artistic decision and whether you want to continue or finish."""
            
            assessment_action = painter.agent.analyze_and_plan(assessment_prompt, current_stage_file)
            assessment_decision = assessment_action.reasoning
            print(f"🎯 Agent's assessment: {assessment_decision}")
            
            # Check the agent's explicit decision
            wants_to_finish = "DECISION: FINISH" in assessment_decision.upper()
            
            if wants_to_finish:
                print(f"🎭 Agent explicitly decided to finish at stage {stage_count}")
                # Execute the final action
                painter.bridge.execute_action(assessment_action)
                break
            else:
                print(f"🔄 Agent wants to continue working...")
                # Execute the action and continue
                painter.bridge.execute_action(assessment_action)
                painter.bridge.capture_canvas(f"stage_{stage_count}.png")
        
        # If we reached max stages, ask for final touches
        if stage_count >= max_stages:
            print(f"\n⏰ Reached maximum stages ({max_stages}). Asking for final touches...")
            final_prompt = f"Your {initial_vision.lower()} artwork has been developed through {stage_count} stages. What final touches would you like to add to complete this piece? End your response with 'DECISION: FINISH' since this is the final stage."
            
            final_action = painter.agent.analyze_and_plan(final_prompt, f"stage_{stage_count}.png")
            final_decision = final_action.reasoning
            print(f"🎯 Final touches: {final_decision}")
            
            painter.bridge.execute_action(final_action)
        
        # Save the final result
        output_filename = f"autonomous_explorer_final.png"
        painter.bridge.capture_canvas(output_filename)
        print(f"✅ Autonomous explorer artwork completed! Saved as '{output_filename}'")
        
        print(f"\n🎉 Autonomous Explorer demo completed successfully!")
        print(f"Generated file: {output_filename}")
        print(f"Total stages: {stage_count}")
        print(f"Agent's creation: {initial_vision}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        painter.close()
        print("\n👋 Autonomous Explorer demo finished. Browser closed.")

if __name__ == "__main__":
    main() 