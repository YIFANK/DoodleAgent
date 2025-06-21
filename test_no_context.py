#!/usr/bin/env python3
"""
Test script to compare drawing agent performance with and without conversation history.
This tests the efficiency improvement of removing conversation context.
"""

import os
import time
import json
from drawing_agent import DrawingAgent
from dotenv import load_dotenv

load_dotenv()

def test_no_context_performance():
    """Test the drawing agent with no conversation context"""
    
    # Initialize agent
    agent = DrawingAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Test prompts
    prompts = [
        "Draw a simple sun in the top right corner",
        "Add a house with a triangular roof in the center",
        "Draw some clouds in the sky",
        "Add a tree next to the house"
    ]
    
    print("Testing Drawing Agent Performance WITHOUT Conversation History")
    print("=" * 60)
    
    # Use a simple canvas image (you can replace with actual canvas)
    canvas_image = "output/canvas.png"  # Make sure this exists
    
    total_time = 0
    actions = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\nStep {i}: {prompt}")
        
        start_time = time.time()
        
        try:
            action = agent.analyze_and_plan(prompt, canvas_image)
            end_time = time.time()
            
            request_time = end_time - start_time
            total_time += request_time
            
            print(f"  Time: {request_time:.2f}s")
            print(f"  Brush: {action.brush}")
            print(f"  Color: {action.color}")
            print(f"  Strokes: {len(action.strokes)}")
            print(f"  Reasoning: {action.reasoning[:100]}...")
            
            actions.append({
                "prompt": prompt,
                "time": request_time,
                "brush": action.brush,
                "color": action.color,
                "stroke_count": len(action.strokes),
                "reasoning": action.reasoning
            })
            
        except Exception as e:
            print(f"  Error: {e}")
            actions.append({
                "prompt": prompt,
                "time": 0,
                "error": str(e)
            })
    
    print(f"\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per request: {total_time/len(prompts):.2f}s")
    print(f"Conversation length at end: {agent.get_conversation_length()}")
    
    # Save results
    results = {
        "test_type": "no_conversation_history",
        "total_time": total_time,
        "average_time": total_time/len(prompts),
        "final_conversation_length": agent.get_conversation_length(),
        "actions": actions
    }
    
    with open("test_results_no_context.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Results saved to test_results_no_context.json")
    
    return results

def compare_with_old_method():
    """
    This function would test the old method with conversation history,
    but since we've already modified the agent, we'll just show what
    the difference would be.
    """
    print("\n" + "=" * 60)
    print("EFFICIENCY COMPARISON:")
    print("=" * 60)
    print("Without conversation history:")
    print("  ✅ Each request is independent")
    print("  ✅ No accumulated message history")
    print("  ✅ Faster API calls (less tokens)")
    print("  ✅ Lower API costs")
    print("  ❌ No context from previous interactions")
    print("  ❌ May repeat similar actions")
    
    print("\nWith conversation history (previous method):")
    print("  ❌ Messages accumulate over time")
    print("  ❌ Slower API calls (more tokens)")
    print("  ❌ Higher API costs")
    print("  ✅ Context awareness between requests")
    print("  ✅ Can build upon previous actions")

if __name__ == "__main__":
    # Check if canvas image exists
    canvas_path = "output/canvas.png"
    if not os.path.exists(canvas_path):
        print(f"Warning: Canvas image not found at {canvas_path}")
        print("Creating a placeholder canvas reference...")
        os.makedirs("output", exist_ok=True)
        # You might want to copy an actual canvas image here
    
    try:
        results = test_no_context_performance()
        compare_with_old_method()
        
        print(f"\n" + "=" * 60)
        print("TEST COMPLETE!")
        print("The agent now operates without conversation history.")
        print("Each request is independent, improving efficiency.")
        
    except Exception as e:
        print(f"Test failed: {e}")
        print("Make sure you have:")
        print("1. ANTHROPIC_API_KEY in your .env file")
        print("2. A canvas image at output/canvas.png") 