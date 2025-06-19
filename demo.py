#!/usr/bin/env python3
"""
Demo script for the Drawing Agent system.
This script demonstrates how to use the LLM-powered drawing agent
to create artwork based on text prompts.
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
        print("🎨 Starting Drawing Agent Demo")
        print("=" * 50)
        
        # Start the painting interface
        painter.start()
        
        # Demo 1: Simple landscape
        print("\n🌄 Demo 1: Creating a simple landscape")
        landscape_prompts = [
            "Draw a bright blue sky with white fluffy clouds",
            "Add green rolling hills in the middle ground",
            "Create a small lake in the foreground with blue water",
            "Add a few trees scattered around the landscape"
        ]
        
        print("Executing landscape prompts...")
        actions = painter.paint_sequence(landscape_prompts)
        
        # Save the result
        painter.bridge.capture_canvas("demo_landscape.png")
        print("✅ Landscape completed! Saved as 'demo_landscape.png'")
        
        # Clear canvas for next demo
        painter.bridge.clear_canvas()
        
        # Demo 2: Abstract art
        print("\n🎭 Demo 2: Creating abstract art")
        abstract_prompts = [
            "Create flowing particle effects in red and orange",
            "Add swirling blue and purple watercolor patterns",
            "Include some bold black crayon strokes for contrast",
            "Finish with some thick oil paint dabs in yellow"
        ]
        
        print("Executing abstract art prompts...")
        actions = painter.paint_sequence(abstract_prompts)
        
        # Save the result
        painter.bridge.capture_canvas("demo_abstract.png")
        print("✅ Abstract art completed! Saved as 'demo_abstract.png'")
        
        # Clear canvas for next demo
        painter.bridge.clear_canvas()
        
        # Demo 3: Portrait sketch
        print("\n👤 Demo 3: Creating a portrait sketch")
        portrait_prompts = [
            "Sketch the basic outline of a face with crayon",
            "Add hair using flowing particle effects",
            "Create eyes and nose with oil paint details",
            "Add a subtle background with watercolor"
        ]
        
        print("Executing portrait prompts...")
        actions = painter.paint_sequence(portrait_prompts)
        
        # Save the result
        painter.bridge.capture_canvas("demo_portrait.png")
        print("✅ Portrait completed! Saved as 'demo_portrait.png'")
        
        print("\n🎉 All demos completed successfully!")
        print("Generated files:")
        print("  - demo_landscape.png")
        print("  - demo_abstract.png") 
        print("  - demo_portrait.png")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        painter.close()
        print("\n👋 Demo finished. Browser closed.")

if __name__ == "__main__":
    main() 