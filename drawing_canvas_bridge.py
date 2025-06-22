#!/usr/bin/env python3
"""
Bridge for drawing_canvas.html
This module provides integration between the FreeDrawingAgent and the drawing_canvas.html interface.
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from free_drawing_agent import FreeDrawingAgent, DrawingInstruction
import base64
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class DrawingCanvasBridge:
    """
    Bridge between the FreeDrawingAgent and the drawing_canvas.html interface.
    Handles the execution of drawing instructions on the HTML canvas.
    """

    def __init__(self, canvas_url: str = None):
        self.canvas_url = canvas_url or f"file://{os.path.abspath('drawing_canvas.html')}"
        self.driver = None
        self.canvas = None
        self.wait = None

    def start_canvas_interface(self):
        """Initialize the web driver and load the drawing canvas interface"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # Uncomment for headless mode
        # options.add_argument("--headless")

        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.canvas_url)

        # Wait for the canvas to be ready
        self.wait = WebDriverWait(self.driver, 10)

        # The canvas in drawing_canvas.html is created by p5.js and located in #p5-canvas
        self.canvas = self.wait.until(
            EC.presence_of_element_located((By.ID, "p5-canvas"))
        )

        # Wait a bit more for p5.js to fully initialize
        time.sleep(2)

        print("Drawing canvas interface loaded successfully")

    def set_brush(self, brush_type: str):
        """Set the brush type in the interface using the brush buttons"""
        try:
            # Map brush types to button classes in drawing_canvas.html
            brush_button_map = {
                "pen": "pen",
                "marker": "marker",
                "crayon": "crayon",
                "wiggle": "wiggle",
                "spray": "spray",
                "fountain": "fountain"
            }

            if brush_type not in brush_button_map:
                print(f"Error: Invalid brush type '{brush_type}'")
                print(f"Available brush types: {list(brush_button_map.keys())}")
                brush_type = "pen"  # Use default

            # Click the appropriate brush button
            brush_class = brush_button_map[brush_type]
            brush_button = self.driver.find_element(By.CSS_SELECTOR, f".brush-btn.{brush_class}")
            brush_button.click()

            time.sleep(0.5)  # Wait for brush to be set

        except Exception as e:
            print(f"Error setting brush '{brush_type}': {e}")
            # Try to set default pen brush
            try:
                pen_button = self.driver.find_element(By.CSS_SELECTOR, ".brush-btn.pen")
                pen_button.click()
                time.sleep(0.5)
            except:
                print("Failed to set default pen brush")

    def execute_stroke(self, stroke: dict):
        """Execute a single stroke on the canvas"""
        if not self.canvas:
            print("Warning: Canvas not initialized, skipping stroke")
            return

        # Handle multi-point stroke
        if "x" in stroke and "y" in stroke:
            x_coords = stroke["x"]
            y_coords = stroke["y"]

            if len(x_coords) != len(y_coords) or len(x_coords) < 2:
                print(f"Warning: Invalid stroke, need at least 2 points")
                return

            # Execute as a continuous stroke using JavaScript
            self._execute_continuous_stroke(x_coords, y_coords)

    def _execute_continuous_stroke(self, x_coords: list, y_coords: list):
        """Execute a continuous stroke using JavaScript mouse events with smooth interpolation"""
        try:
            # Create JavaScript code to simulate drawing
            js_code = f"""
            // Get the canvas element
            const canvasElement = document.querySelector('#p5-canvas canvas');
            if (!canvasElement) {{
                console.error('Canvas not found');
                return;
            }}

            const rect = canvasElement.getBoundingClientRect();
            const x_coords = {x_coords};
            const y_coords = {y_coords};

            console.log('Starting smooth stroke with coordinates:', x_coords, y_coords);
            console.log('Initial pmouseX, pmouseY:', window.pmouseX, window.pmouseY);
            console.log('Initial mouseX, mouseY:', window.mouseX, window.mouseY);

            // Simulate mouse events for drawing
            function simulateMouseEvent(type, x, y) {{
                const event = new MouseEvent(type, {{
                    clientX: x + rect.left,
                    clientY: y + rect.top,
                    bubbles: true,
                    cancelable: true,
                    view: window
                }});
                canvasElement.dispatchEvent(event);
            }}

            // Linear interpolation function
            function lerp(start, end, t) {{
                return start + (end - start) * t;
            }}

            // CRITICAL FIX: Directly set p5.js mouse variables to prevent large first shape
            const startX = x_coords[0];
            const startY = y_coords[0];

            // Set both current and previous mouse positions to the starting point
            if (typeof window.mouseX !== 'undefined') {{
                window.pmouseX = startX;
                window.pmouseY = startY;
                window.mouseX = startX;
                window.mouseY = startY;
                console.log('Manually set mouse positions to:', startX, startY);
            }}

            // Also try setting the global variables that p5.js might use
            if (typeof pmouseX !== 'undefined') {{
                pmouseX = startX;
                pmouseY = startY;
                mouseX = startX;
                mouseY = startY;
            }}

            // Now start the drawing sequence
            simulateMouseEvent('mousedown', startX, startY);

            // Small delay after mousedown, then start moving
            setTimeout(() => {{
                console.log('Starting smooth movement - pmouseX:', window.pmouseX, 'pmouseY:', window.pmouseY);

                // Create smooth interpolated movement between points
                let currentPointIndex = 0;
                const segmentDuration = 200; // 200ms between main points
                const interpolationSteps = 4; // Number of intermediate points per segment
                const stepDuration = segmentDuration / interpolationSteps; // ~20ms per step

                function drawNextSegment() {{
                    if (currentPointIndex >= x_coords.length - 1) {{
                        // End the stroke
                        setTimeout(() => {{
                            simulateMouseEvent('mouseup', x_coords[x_coords.length - 1], y_coords[y_coords.length - 1]);
                            console.log('Smooth stroke completed');
                        }}, stepDuration);
                        return;
                    }}

                    const startX = x_coords[currentPointIndex];
                    const startY = y_coords[currentPointIndex];
                    const endX = x_coords[currentPointIndex + 1];
                    const endY = y_coords[currentPointIndex + 1];

                    // Create smooth interpolation between current and next point
                    for (let step = 1; step <= interpolationSteps; step++) {{
                        setTimeout(() => {{
                            const t = step / interpolationSteps;
                            const interpX = lerp(startX, endX, t);
                            const interpY = lerp(startY, endY, t);
                            
                            simulateMouseEvent('mousemove', interpX, interpY);
                            
                            // If this is the last step of this segment, move to next segment
                            if (step === interpolationSteps) {{
                                currentPointIndex++;
                                setTimeout(drawNextSegment, stepDuration);
                            }}
                        }}, step * stepDuration);
                    }}
                }}

                // Start drawing the first segment
                drawNextSegment();
            }}, 100);  // Reduced initial delay
            """

            self.driver.execute_script(js_code)

            # Wait for the stroke to complete (200ms per segment + some buffer)
            total_duration = len(x_coords) * 0.2 + 0.5
            time.sleep(total_duration)

        except Exception as e:
            print(f"Warning: Stroke execution failed: {e}")

    def execute_instruction(self, instruction: DrawingInstruction):
        """Execute a complete drawing instruction"""
        print(f"Executing instruction: {instruction.reasoning}")
        print(f"Using brush: {instruction.brush}, color: {instruction.color}")

        # Set the brush
        self.set_brush(instruction.brush)

        # Note: Color setting might not work for all brushes in drawing_canvas.html
        # since some brushes (like crayon) have their own color behavior

        # Execute all strokes
        for i, stroke in enumerate(instruction.strokes):
            print(f"  Drawing stroke {i+1}/{len(instruction.strokes)}: {stroke['description']}")

            # Show timing information if available
            if 'timing' in stroke and 'original_x' in stroke:
                original_points = len(stroke['original_x'])
                interpolated_points = len(stroke['x'])
                print(f"    Original points: {original_points}, Interpolated points: {interpolated_points}")
                print(f"    Timing: {stroke['timing']}")

            self.execute_stroke(stroke)

    def capture_canvas(self, filename: str = "current_canvas.png"):
        """Capture the current canvas as an image"""
        try:
            # Use p5.js save function to capture the canvas
            js_code = """
            // Get the p5 canvas and convert to data URL
            const canvas = document.querySelector('#p5-canvas canvas');
            return canvas.toDataURL('image/png');
            """

            data_url = self.driver.execute_script(js_code)

            # Remove the data URL prefix
            image_data = data_url.split(',')[1]

            # Decode and save the image
            image_bytes = base64.b64decode(image_data)
            with open(filename, 'wb') as f:
                f.write(image_bytes)

            print(f"Canvas captured and saved as '{filename}'")
            return filename

        except Exception as e:
            print(f"Error capturing canvas: {e}")
            return None

    def clear_canvas(self):
        """Clear the canvas using the clear button"""
        try:
            clear_button = self.driver.find_element(By.CSS_SELECTOR, ".clear-btn")
            clear_button.click()
            time.sleep(0.5)
            print("Canvas cleared")
        except Exception as e:
            print(f"Error clearing canvas: {e}")

    def close(self):
        """Close the web driver"""
        if self.driver:
            self.driver.quit()
            print("Canvas interface closed")

class AutomatedDrawingCanvas:
    """
    High-level interface that combines the FreeDrawingAgent with the DrawingCanvasBridge
    for automated creative drawing sessions.
    """

    def __init__(self, api_key: str, canvas_url: str = None):
        self.agent = FreeDrawingAgent(api_key=api_key)
        self.bridge = DrawingCanvasBridge(canvas_url=canvas_url)

    def start(self):
        """Start the drawing canvas interface"""
        self.bridge.start_canvas_interface()

    def draw_from_canvas(self, canvas_filename: str = "current_canvas.png",
                        question: str = "What would you like to draw next?"):
        """
        Analyze the current canvas and execute a drawing instruction.

        Args:
            canvas_filename: Filename to save/load the current canvas
            question: Question to ask the agent about what to draw

        Returns:
            The executed DrawingInstruction
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)

        # Get drawing instruction from agent
        instruction = self.agent.create_drawing_instruction(canvas_filename, question)

        # Execute the instruction
        self.bridge.execute_instruction(instruction)

        return instruction

    def draw_from_emotion(self, canvas_filename: str = "current_canvas.png",
                         emotion: str = None):
        """
        Create a mood-based drawing instruction and execute it.

        Args:
            canvas_filename: Filename to save the current canvas image
            emotion: Optional emotion to express (if None, LLM chooses autonomously)

        Returns:
            DrawingInstruction object that was executed
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)

        # Create mood-based drawing instruction
        instruction = self.agent.create_emotion_drawing_instruction(
            canvas_filename, emotion
        )

        # Execute the instruction
        self.bridge.execute_instruction(instruction)

        return instruction

    def draw_from_abstract(self, canvas_filename: str = "current_canvas.png"):
        """
        Create an abstract, non-representational drawing instruction and execute it.

        Args:
            canvas_filename: Filename to save the current canvas image

        Returns:
            DrawingInstruction object that was executed
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)

        # Create abstract drawing instruction
        instruction = self.agent.create_abstract_drawing_instruction(
            canvas_filename
        )

        # Execute the instruction
        self.bridge.execute_instruction(instruction)

        return instruction

    def creative_session(self, num_iterations: int = 5,output_dir: str = 'output'):
        """
        Run a creative drawing session with multiple iterations.

        Args:
            num_iterations: Number of drawing iterations to perform
        """
        print(f"🎨 Starting creative drawing session with {num_iterations} iterations")

        # Create output directory
        os.makedirs(f"{output_dir}", exist_ok=True)

        # Capture initial blank canvas
        self.bridge.capture_canvas(f"{output_dir}/canvas_step_0.png")

        instructions = []

        for i in range(num_iterations):
            print(f"\n--- Iteration {i+1}/{num_iterations} ---")

            canvas_file = f"output/canvas_step_{i}.png"

            # Questions to vary the creative process
            questions = [
                "What would you like to draw next?",
                "How can you enhance this artwork?",
                "What creative element would complement this scene?",
                "What interesting detail could you add?",
                "How would you continue this artistic expression?"
            ]

            question = questions[i % len(questions)]

            instruction = self.draw_from_canvas(canvas_file, question)
            instructions.append(instruction)

            # Capture the result
            self.bridge.capture_canvas(f"{output_dir}/canvas_step_{i+1}.png")

            print(f"Agent's reasoning: {instruction.reasoning}")

        # Save final artwork
        final_canvas = "output/final_artwork.png"
        self.bridge.capture_canvas(final_canvas)

        print(f"\n🎉 Creative session completed!")
        print(f"Final artwork saved as: {final_canvas}")
        print(f"\n📋 Session Summary:")
        for i, instruction in enumerate(instructions):
            print(f"  Step {i+1}: {instruction.reasoning}")

        return instructions

    def close(self):
        """Close the drawing canvas interface"""
        # Finalize agent session logs
        self.agent.close_session_logs()
        self.bridge.close()

def main():
    """Example usage of the AutomatedDrawingCanvas"""
    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return

    # Create the automated drawing canvas
    canvas = AutomatedDrawingCanvas(api_key=api_key)

    try:
        # Start the interface
        canvas.start()

        # Run a creative session
        canvas.creative_session(num_iterations=3)

    except KeyboardInterrupt:
        print("\n⚠️ Session interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during session: {e}")
        import traceback
        traceback.print_exc()

    finally:
        canvas.close()

if __name__ == "__main__":
    main()
