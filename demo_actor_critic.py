#!/usr/bin/env python3
"""
Demo script for Actor-Critic Brush Explorer
Demonstrates different usage patterns and configurations
"""

import os
import sys
from dotenv import load_dotenv
from actor_critic_explorer import ActorCriticExplorer

load_dotenv()

def demo_basic_exploration():
    """Basic exploration demo with default settings"""
    print("🎨 === BASIC EXPLORATION DEMO ===")
    print("This demo runs the actor-critic system with default settings.")
    print("The agent will explore brushes freely with critic feedback.\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set ANTHROPIC_API_KEY in your .env file")
        return
    
    explorer = ActorCriticExplorer(api_key)
    explorer.explore_brushes(max_stages=15, output_dir="demo_basic")
    print("✅ Basic exploration complete! Check 'demo_basic' folder for results.")

def demo_focused_exploration():
    """Focused exploration with specific goals"""
    print("\n🎯 === FOCUSED EXPLORATION DEMO ===")
    print("This demo shows how to customize artistic goals for more directed exploration.\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set ANTHROPIC_API_KEY in your .env file")
        return
    
    explorer = ActorCriticExplorer(api_key)
    
    # Override the artistic goals with more specific ones
    explorer.artistic_goals = [
        "Create a vibrant abstract landscape using watercolor and oil brushes",
        "Build a geometric composition using pen and marker tools",
        "Experiment with textural effects using crayon and oil paint techniques"
    ]
    
    explorer.explore_brushes(max_stages=20, output_dir="demo_focused")
    print("✅ Focused exploration complete! Check 'demo_focused' folder for results.")

def demo_quick_exploration():
    """Quick exploration for testing"""
    print("\n⚡ === QUICK EXPLORATION DEMO ===")
    print("This demo runs a short exploration session for quick testing.\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set ANTHROPIC_API_KEY in your .env file")
        return
    
    explorer = ActorCriticExplorer(api_key)
    explorer.explore_brushes(max_stages=8, output_dir="demo_quick")
    print("✅ Quick exploration complete! Check 'demo_quick' folder for results.")

def demo_extended_exploration():
    """Extended exploration session"""
    print("\n🚀 === EXTENDED EXPLORATION DEMO ===")
    print("This demo runs an extended session to see the full capabilities of the system.")
    print("The agent will have more time to develop complex artworks.\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set ANTHROPIC_API_KEY in your .env file")
        return
    
    explorer = ActorCriticExplorer(api_key)
    explorer.explore_brushes(max_stages=40, output_dir="demo_extended")
    print("✅ Extended exploration complete! Check 'demo_extended' folder for results.")

def demo_brush_specific():
    """Demo focusing on specific brush types"""
    print("\n🖌️ === BRUSH-SPECIFIC EXPLORATION DEMO ===")
    print("This demo shows how to create a custom explorer that focuses on specific brushes.\n")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: Please set ANTHROPIC_API_KEY in your .env file")
        return
    
    explorer = ActorCriticExplorer(api_key)
    
    # Modify the actor to focus on specific brushes
    explorer.actor.available_brushes = ["watercolor", "oil", "crayon", "pen"]
    explorer.artistic_goals = [
        "Create a traditional painting effect using watercolor and oil brushes",
        "Combine crayon texture with pen precision for mixed media effects", 
        "Explore the contrast between organic watercolor and precise pen techniques"
    ]
    
    explorer.explore_brushes(max_stages=25, output_dir="demo_brush_specific")
    print("✅ Brush-specific exploration complete! Check 'demo_brush_specific' folder for results.")

def main():
    """Main demo selection interface"""
    print("🎭 Actor-Critic Brush Explorer Demo")
    print("=" * 50)
    print("Select a demo to run:")
    print("1. Basic Exploration (15 stages)")
    print("2. Focused Exploration (20 stages)")
    print("3. Quick Test (8 stages)")
    print("4. Extended Session (40 stages)")
    print("5. Brush-Specific Demo (25 stages)")
    print("6. Run All Demos")
    print("0. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == "0":
                print("👋 Goodbye!")
                break
            elif choice == "1":
                demo_basic_exploration()
                break
            elif choice == "2":
                demo_focused_exploration()
                break
            elif choice == "3":
                demo_quick_exploration()
                break
            elif choice == "4":
                demo_extended_exploration()
                break
            elif choice == "5":
                demo_brush_specific()
                break
            elif choice == "6":
                print("🎨 Running all demos in sequence...")
                demo_quick_exploration()
                demo_basic_exploration()
                demo_focused_exploration()
                demo_brush_specific()
                print("\n🎉 All demos completed!")
                break
            else:
                print("❌ Invalid choice. Please enter a number between 0-6.")
                
        except KeyboardInterrupt:
            print("\n⚠️ Demo interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break

if __name__ == "__main__":
    main() 