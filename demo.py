#!/usr/bin/env python3
"""
Demo script for the Drawing Agent system.
This script demonstrates how to use the LLM-powered drawing agent
to create artwork based on autonomous prompt generation.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from painting_bridge import AutomatedPainter

# Load environment variables from .env file
load_dotenv()

def generate_autonomous_prompt(api_key: str, canvas_state: str = "blank", step: int = 1, total_steps: int = 4) -> str:
    """
    Generate an autonomous creative prompt using Claude.

    Args:
        api_key: Anthropic API key
        canvas_state: Description of current canvas state
        step: Current step number
        total_steps: Total number of steps planned

    Returns:
        Generated creative prompt
    """

    system_prompt = """You are a creative, autonomous artist. You create artworks no one has ever seen before to express yourself.

Your mission is to generate unique, creative prompts for drawing that will result in original, expressive artwork. Each prompt should be:
- Creative and unexpected
- Specific enough to guide drawing actions
- Open to artistic interpretation
- Focused on creating something truly original

Respond with a single, creative drawing prompt that captures your artistic vision."""

    user_prompt = f"""Generate a creative drawing prompt for step {step} of {total_steps}.

Current canvas state: {canvas_state}

Create a prompt that will result in unique, expressive artwork that no one has ever seen before. Be creative, unexpected, and artistic.

Respond with just the creative prompt, nothing else."""

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01"
    }

    data = {
        "model": "claude-3-5-haiku-20241022",
        "max_tokens": 200,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        response.raise_for_status()

        result = response.json()
        prompt = result["content"][0]["text"].strip()

        # Clean up the prompt if it has quotes or extra formatting
        if prompt.startswith('"') and prompt.endswith('"'):
            prompt = prompt[1:-1]
        if prompt.startswith("'") and prompt.endswith("'"):
            prompt = prompt[1:-1]

        return prompt

    except Exception as e:
        print(f"Error generating autonomous prompt: {e}")
        # Fallback prompts if API fails
        fallback_prompts = [
            "Create flowing energy patterns in unexpected colors",
            "Draw geometric shapes that seem to defy gravity",
            "Paint organic forms that emerge from abstract chaos",
            "Add ethereal light effects that dance across the canvas"
        ]
        return fallback_prompts[step - 1] if step <= len(fallback_prompts) else "Create something beautiful and unexpected"

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
        print("🎨 Starting Autonomous Drawing Agent Demo")
        print("=" * 50)
        print("🤖 The AI will generate its own creative prompts!")
        print("=" * 50)

        # Start the painting interface
        painter.start()

        # Demo 1: Autonomous creative artwork
        print("\n🎭 Demo 1: Creating autonomous creative artwork")

        # Generate autonomous prompts
        autonomous_prompts = []
        canvas_state = "blank canvas"

        for step in range(1, 5):  # Generate 4 autonomous prompts
            print(f"\n🤖 Generating autonomous prompt {step}/4...")
            prompt = generate_autonomous_prompt(api_key, canvas_state, step, 4)
            autonomous_prompts.append(prompt)
            print(f"Generated prompt: {prompt}")
            canvas_state = f"canvas with {step} elements added"

        print("\nExecuting autonomous prompts...")
        actions = painter.paint_sequence(autonomous_prompts)

        # Save the result
        painter.bridge.capture_canvas("demo_autonomous.png")
        print("✅ Autonomous artwork completed! Saved as 'demo_autonomous.png'")

        # Clear canvas for next demo
        painter.bridge.clear_canvas()

        # Demo 2: Another autonomous creation
        print("\n🌟 Demo 2: Creating another autonomous artwork")

        # Generate new autonomous prompts
        autonomous_prompts_2 = []
        canvas_state = "blank canvas"

        for step in range(1, 4):  # Generate 3 more autonomous prompts
            print(f"\n🤖 Generating autonomous prompt {step}/3...")
            prompt = generate_autonomous_prompt(api_key, canvas_state, step, 3)
            autonomous_prompts_2.append(prompt)
            print(f"Generated prompt: {prompt}")
            canvas_state = f"canvas with {step} elements added"

        print("\nExecuting second set of autonomous prompts...")
        actions = painter.paint_sequence(autonomous_prompts_2)

        # Save the result
        painter.bridge.capture_canvas("demo_autonomous_2.png")
        print("✅ Second autonomous artwork completed! Saved as 'demo_autonomous_2.png'")

        print("\n🎉 All autonomous demos completed successfully!")
        print("Generated files:")
        print("  - demo_autonomous.png")
        print("  - demo_autonomous_2.png")
        print("\n🤖 The AI created unique artwork using its own creative prompts!")

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
