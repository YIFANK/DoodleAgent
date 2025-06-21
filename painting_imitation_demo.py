#!/usr/bin/env python3
"""
Painting Imitation Demo script for the Drawing Agent system.
This script tests the agent's ability to imitate an existing painting
by analyzing an input image and drawing something as close as possible to it.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from painting_bridge import AutomatedPainter

# Load environment variables from .env file
load_dotenv()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Painting Imitation Demo')
    parser.add_argument('--input-image', '-i', required=True, 
                       help='Path to the input image to imitate')
    parser.add_argument('--output-prefix', '-o', default='imitation',
                       help='Prefix for output files (default: imitation)')
    parser.add_argument('--max-stages', '-m', type=int, default=30,
                       help='Maximum number of imitation stages (default: 30)')
    parser.add_argument('--output-dir', '-d', default='output',
                       help='Output directory for all files (default: output)')
    args = parser.parse_args()
    
    # Check if input image exists
    if not os.path.exists(args.input_image):
        print(f"Error: Input image '{args.input_image}' not found")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        print("Create a .env file with: ANTHROPIC_API_KEY=your-api-key-here")
        sys.exit(1)
    
    # Get the path to the painter.html file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    painter_url = f"file://{current_dir}/allbrush.html"
    
    # Initialize the automated painter
    painter = AutomatedPainter(api_key=api_key, painter_url=painter_url)
    
    try:
        print("🎨 Starting Structured Painting Imitation Demo")
        print("=" * 65)
        print(f"🖼️  Target image: {args.input_image}")
        print(f"📁 Output directory: {args.output_dir}")
        print(f"📝 Output prefix: {args.output_prefix}")
        print(f"🔄 Max stages: {args.max_stages}")
        print("=" * 65)
        print("🤖 The agent will:")
        print("   1. Analyze and break down the target image into components")
        print("   2. Create a structured imitation plan")
        print("   3. Work on specific components in each stage")
        print("=" * 65)
        
        # Start the painting interface
        painter.start()
        
        # Capture initial blank canvas
        initial_canvas_path = os.path.join(args.output_dir, f"{args.output_prefix}_stage_0.png")
        painter.bridge.capture_canvas(initial_canvas_path)
        
        # Create a temporary copy of the target image for the agent to analyze
        import shutil
        target_copy = os.path.join(args.output_dir, f"{args.output_prefix}_target.png")
        shutil.copy2(args.input_image, target_copy)
        
        # STAGE 1: Component Analysis
        print(f"\n🔍 Stage 1: Agent is analyzing the target image components...")
        analysis_prompt = """You are a skilled artist analyzing a target image for imitation. Your task is to break down this image into its major visual components and elements.

COMPONENT ANALYSIS INSTRUCTIONS:
1. Identify all major shapes, objects, and regions in the image
2. Note their colors (provide specific hex codes when possible)
3. Describe their approximate positions and sizes
4. Identify the layering order (background to foreground)
5. Note any textures, patterns, or special effects

Please provide your analysis in this structured format:

MAJOR COMPONENTS:
- Component 1: [Name] - [Color/hex code] - [Position] - [Size] - [Layer]
- Component 2: [Name] - [Color/hex code] - [Position] - [Size] - [Layer]
- Component 3: [Name] - [Color/hex code] - [Position] - [Size] - [Layer]
(continue for all major components)

OVERALL COMPOSITION:
- Background elements: [describe]
- Midground elements: [describe]  
- Foreground elements: [describe]
- Color palette: [list main colors with hex codes]
- Style notes: [artistic style, brush techniques, etc.]

Example for a landscape:
MAJOR COMPONENTS:
- Sky: #87CEEB (light blue) - Top third - Large - Background layer
- Mountains: #708090 (gray) - Middle distance - Medium - Background layer  
- Trees: #228B22 (forest green) - Mid-ground - Various sizes - Middle layer
- Grass: #90EE90 (light green) - Bottom third - Large - Foreground layer

End your analysis with "ANALYSIS COMPLETE" to proceed to planning."""
        
        # Use direct chat for analysis (no drawing action needed)
        import base64
        
        # Read and encode the target image
        with open(target_copy, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        analysis_response = painter.agent.client.messages.create(
            model=painter.agent.model,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analysis_prompt
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        )
        
        component_analysis = analysis_response.content[0].text
        print(f"🎯 Component Analysis: {component_analysis}")
        
        # STAGE 2: Imitation Planning
        print(f"\n📋 Stage 2: Agent is creating imitation plan...")
        planning_prompt = f"""Based on your component analysis, create a detailed step-by-step plan for imitating this image.

YOUR PREVIOUS ANALYSIS:
{component_analysis}

PLANNING INSTRUCTIONS:
Create a logical sequence for recreating the image. Consider:
1. Start with background elements first
2. Build up layers from back to front
3. Establish basic shapes before details
4. Match colors accurately
5. Use appropriate brushes for different textures

Available brush types: watercolor, crayon, oil, pen, marker, rainbow, wiggle, spray, fountain, splatter, toothpick

Please provide your plan in this format:

IMITATION PLAN:
Step 1: [Component name] - [Brush type] - [Color] - [Technique/approach]
Step 2: [Component name] - [Brush type] - [Color] - [Technique/approach]
Step 3: [Component name] - [Brush type] - [Color] - [Technique/approach]
(continue for all steps)

BRUSH SELECTION RATIONALE:
- [Brush type]: Best for [specific use case]
- [Brush type]: Best for [specific use case]

EXPECTED CHALLENGES:
- [Challenge 1 and strategy]
- [Challenge 2 and strategy]

End your response with "PLAN READY" to begin implementation."""
        
        # Use direct chat for planning (no drawing action needed)
        planning_response = painter.agent.client.messages.create(
            model=painter.agent.model,
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": planning_prompt
                }
            ]
        )
        
        imitation_plan = planning_response.content[0].text
        print(f"🎯 Imitation Plan: {imitation_plan}")
        
        # STAGE 3: Begin Implementation
        print(f"\n🎨 Stage 3: Agent begins implementing the plan...")
        initial_prompt = f"""Now begin implementing your imitation plan. Start with the first step from your plan.

YOUR COMPONENT ANALYSIS:
{component_analysis}

YOUR IMITATION PLAN:
{imitation_plan}

IMPLEMENTATION INSTRUCTIONS:
1. Focus on the first component/step from your plan
2. Use the specified brush type and color
3. Create the basic shape and structure first
4. Don't worry about perfection - build up gradually
5. Use hex color codes for accurate color matching

Begin with your first planned step. Make clear, deliberate strokes to establish the foundation of your imitation."""
        
        initial_action = painter.agent.analyze_and_plan_with_target(initial_prompt, initial_canvas_path, target_copy)
        initial_vision = initial_action.reasoning
        print(f"🎯 Agent's implementation start: {initial_vision}")
        
        # Execute the initial action
        painter.bridge.execute_action(initial_action)
        stage_1_path = os.path.join(args.output_dir, f"{args.output_prefix}_stage_1.png")
        painter.bridge.capture_canvas(stage_1_path)
        
        # Component-focused imitation loop
        stage_count = 1
        max_stages = args.max_stages
        imitation_progress = [f"Analysis: {component_analysis}", f"Plan: {imitation_plan}", initial_vision]
        
        while stage_count < max_stages:
            stage_count += 1
            current_stage_file = os.path.join(args.output_dir, f"{args.output_prefix}_stage_{stage_count-1}.png")
            
            print(f"\n🎨 Implementation Stage {stage_count}: Agent works on specific components...")
            
            # Component-focused refinement prompt
            component_prompt = f"""Continue implementing your imitation plan. Compare your current progress with the target image and your original plan.

YOUR ORIGINAL ANALYSIS:
{component_analysis}

YOUR ORIGINAL PLAN:
{imitation_plan}

CURRENT TASK:
1. Look at your current canvas and compare it to the target image
2. Identify which components from your analysis still need work:
   - Which components are missing entirely?
   - Which components are present but need refinement?
   - Which components have wrong colors, shapes, or positions?
3. Choose ONE specific component to focus on in this stage
4. Work on that component using the appropriate brush and colors

COMPONENT FOCUS APPROACH:
- State clearly which component you're working on
- Explain why this component needs attention
- Use the correct colors (hex codes) for that component
- Use the appropriate brush type for the texture/effect needed
- Make focused, purposeful strokes for that component only

DECISION MAKING:
- If major components are still missing or very rough: CONTINUE
- If all major components are present and reasonably accurate: FINISH

IMPORTANT: At the end of your response, clearly state:
- Which component you focused on in this stage
- Your satisfaction level:
  * "SATISFACTION: CONTINUE" if more work is needed
  * "SATISFACTION: FINISH" if you're satisfied with the overall result

What specific component will you work on next?"""
            
            imitation_action = painter.agent.analyze_and_plan_with_target(component_prompt, current_stage_file, target_copy)
            imitation_decision = imitation_action.reasoning
            imitation_progress.append(imitation_decision)
            print(f"🎯 Component focus: {imitation_decision}")
            
            # Check the agent's satisfaction level
            wants_to_finish = "SATISFACTION: FINISH" in imitation_decision.upper()
            
            if wants_to_finish:
                print(f"✅ Agent is satisfied with the component-based imitation!")
                # Execute the final action
                painter.bridge.execute_action(imitation_action)
                break
            else:
                print(f"🔄 Agent continues working on specific components...")
                # Execute the action and continue
                painter.bridge.execute_action(imitation_action)
                next_stage_path = os.path.join(args.output_dir, f"{args.output_prefix}_stage_{stage_count}.png")
                painter.bridge.capture_canvas(next_stage_path)
        
        # If we reached max stages, give one final opportunity
        if stage_count >= max_stages:
            print(f"\n⏰ Maximum imitation time reached. Final component refinement...")
            final_prompt = f"""You've been working on component-based imitation for {stage_count} stages. 

YOUR ORIGINAL ANALYSIS:
{component_analysis}

This is your final opportunity to refine any remaining components to better match the target image.

Choose the most important component that still needs improvement and make your final adjustments.

End your response with "SATISFACTION: FINISH" since this is the final stage."""
            
            final_stage_path = os.path.join(args.output_dir, f"{args.output_prefix}_stage_{stage_count}.png")
            final_action = painter.agent.analyze_and_plan_with_target(final_prompt, final_stage_path, target_copy)
            final_decision = final_action.reasoning
            imitation_progress.append(f"Final component refinement: {final_decision}")
            print(f"🎯 Final component work: {final_decision}")
            
            painter.bridge.execute_action(final_action)
        
        # Save the final result
        output_filename = os.path.join(args.output_dir, f"{args.output_prefix}_final_imitation.png")
        painter.bridge.capture_canvas(output_filename)
        print(f"✅ Component-based painting imitation completed! Saved as '{output_filename}'")
        
        # Clean up temporary files
        if os.path.exists(target_copy):
            os.remove(target_copy)
        
        print(f"\n🎉 Structured Painting Imitation demo completed successfully!")
        print(f"Generated files in '{args.output_dir}':")
        print(f"  - Final imitation: {args.output_prefix}_final_imitation.png")
        print(f"  - Stage images: {args.output_prefix}_stage_*.png")
        print(f"Total imitation stages: {stage_count}")
        print(f"\n📋 Imitation Progress:")
        for i, decision in enumerate(imitation_progress):
            print(f"  Stage {i+1}: {decision[:100]}..." if len(decision) > 100 else f"  Stage {i+1}: {decision}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        painter.close()
        print("\n👋 Structured Painting Imitation demo finished. Browser closed.")

if __name__ == "__main__":
    main() 