#!/usr/bin/env python3
"""
Explorer Demo script for the Drawing Agent system.
This script demonstrates how the LLM-powered drawing agent
can decide what to draw and explore the canvas freely.
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
        print("🎨 Starting Drawing Agent Explorer Demo")
        print("=" * 50)
        
        # Start the painting interface
        painter.start()
        
        # Capture initial blank canvas
        painter.bridge.capture_canvas("blank_canvas.png")
        
        # Ask the agent what it wants to draw by using a creative prompt
        print("\n🤔 Asking the agent what it wants to draw...")
        decision_prompt = "You are an autonomous artist with a blank canvas. What would you like to create today? Think about something creative and interesting that you'd enjoy drawing. Describe your artistic vision and what elements you'd like to include in your artwork."
        
        # Get the agent's decision by analyzing the blank canvas
        decision_action = painter.agent.analyze_and_plan(decision_prompt, "blank_canvas.png")
        agent_decision = decision_action.reasoning
        print(f"🎯 Agent decided to draw: {agent_decision}")
        
        # Generate exploratory painting prompts based on the agent's decision
        print("\n🎨 Generating exploratory painting sequence...")
        
        # Create prompts that encourage exploration and creativity
        exploratory_prompts = [
            f"Begin your artistic journey by exploring the canvas with {agent_decision.lower()} in mind. Start with a foundational element that sets the mood for your creation.",
            f"Continue building your {agent_decision.lower()} artwork by adding more details and depth. Explore different areas of the canvas and experiment with composition.",
            f"Add complementary elements that enhance your {agent_decision.lower()} creation. Consider how different parts of the canvas can work together harmoniously.",
            f"Refine and enhance the overall composition of your {agent_decision.lower()} artwork. Add finishing touches that bring your vision to life.",
            f"Complete your {agent_decision.lower()} masterpiece with final details and artistic flourishes that showcase your creative expression."
        ]
        
        print("Executing exploratory painting sequence...")
        actions = painter.paint_sequence(exploratory_prompts)
        
        # Save the result
        output_filename = f"explorer_creation.png"
        painter.bridge.capture_canvas(output_filename)
        print(f"✅ Explorer artwork completed! Saved as '{output_filename}'")
        
        print("\n🎉 Explorer demo completed successfully!")
        print(f"Generated file: {output_filename}")
        print(f"Agent's creation: {agent_decision}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        painter.close()
        print("\n👋 Explorer demo finished. Browser closed.")

if __name__ == "__main__":
    main() 