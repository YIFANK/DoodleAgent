import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from drawing_agent import DrawingAgent, DrawingAction
import base64
from PIL import Image
import io
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class PaintingBridge:
    """
    Bridge between the DrawingAgent and the painting interface.
    Handles the execution of drawing actions on the HTML canvas.
    """
    
    def __init__(self, painter_url: str = "file:///path/to/allbrush.html"):
        self.painter_url = painter_url
        self.driver = None
        self.canvas = None
        self.wait = None
        
    def start_painting_interface(self):
        """Initialize the web driver and load the painting interface"""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # Uncomment for headless mode
        # options.add_argument("--headless")
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.painter_url)
        
        # Wait for the canvas to be ready
        self.wait = WebDriverWait(self.driver, 10)
        self.canvas = self.wait.until(
            EC.presence_of_element_located((By.ID, "canvas"))
        )
        
        print("Painting interface loaded successfully")
    
    def set_brush(self, brush_type: str):
        """Set the brush type in the interface"""
        try:
            brush_selector = Select(self.driver.find_element(By.ID, "brushSelector"))
            
            # Get all available options for better error reporting
            available_options = [option.get_attribute("value") for option in brush_selector.options]
            
            if brush_type not in available_options:
                print(f"Error: Invalid brush type '{brush_type}'")
                print(f"Available brush types: {available_options}")
                print(f"Using default brush 'flowing' instead")
                brush_type = "flowing"  # Use default
            
            brush_selector.select_by_value(brush_type)
            time.sleep(0.5)  # Wait for brush to load
            
        except Exception as e:
            print(f"Error setting brush '{brush_type}': {e}")
            print("Available brush types: flowing, watercolor, crayon, oil, pen, marker, rainbow, wiggle, spray, fountain, splatter, toothpick")
            # Try to set a default brush
            try:
                brush_selector = Select(self.driver.find_element(By.ID, "brushSelector"))
                brush_selector.select_by_value("flowing")
                time.sleep(0.5)
            except:
                print("Failed to set default brush")
    
    def set_color(self, color: str):
        """Set the brush color"""
        color_input = self.driver.find_element(By.ID, "brushColor")
        self.driver.execute_script(
            f"arguments[0].value = '{color}'; "
            f"arguments[0].dispatchEvent(new Event('input'));", 
            color_input
        )
        time.sleep(0.2)
    
    def execute_stroke(self, stroke: dict):
        """Execute a single stroke on the canvas"""
        if not self.canvas:
            print("Warning: Canvas not initialized, skipping stroke")
            return
            
        # Handle the new simplified stroke format with multiple points
        if "x" in stroke and "y" in stroke:
            # Check if this is a multi-point stroke
            if isinstance(stroke["x"], list) and isinstance(stroke["y"], list):
                # Multi-point stroke - connect points as a continuous stroke
                x_coords = stroke["x"]
                y_coords = stroke["y"]
                
                if len(x_coords) != len(y_coords) or len(x_coords) < 2:
                    print(f"Warning: Invalid multi-point stroke, need at least 2 points")
                    return
                
                # Validate all coordinates
                validated_points = []
                for x, y in zip(x_coords, y_coords):
                    valid_x, valid_y = self._validate_coordinates(x, y)
                    validated_points.append((valid_x, valid_y))
                
                # Execute as a continuous stroke
                self._execute_continuous_stroke(validated_points)
                
            else:
                # Single point stroke (legacy support)
                x, y = stroke["x"], stroke["y"]
                x, y = self._validate_coordinates(x, y)
                self._execute_single_stroke(x, y)
        
        # Legacy support for old stroke format
        elif "type" in stroke and stroke["type"] == "stroke":
            points = stroke.get("points", [])
            if len(points) < 2:
                return
            
            actions = ActionChains(self.driver)
            
            # Execute the stroke point by point
            for i, point in enumerate(points):
                x, y = point["x"], point["y"]
                action = point["action"]
                
                # Validate and sanitize coordinates
                x, y = self._validate_coordinates(x, y)
                
                if action == "mousedown":
                    actions.move_to_element_with_offset(self.canvas, x, y)
                    actions.click_and_hold()
                elif action == "mousemove":
                    actions.move_to_element_with_offset(self.canvas, x, y)
                elif action == "mouseup":
                    actions.move_to_element_with_offset(self.canvas, x, y)
                    actions.release()
            
            try:
                actions.perform()
                time.sleep(0.5)  # Wait for stroke to complete
            except Exception as e:
                print(f"Warning: Legacy stroke execution failed: {e}")
        
        elif stroke.get("type") == "line":
            # Legacy support for line type
            start_x, start_y = stroke["start"]["x"], stroke["start"]["y"]
            end_x, end_y = stroke["end"]["x"], stroke["end"]["y"]
            
            # Validate and sanitize coordinates
            start_x, start_y = self._validate_coordinates(start_x, start_y)
            end_x, end_y = self._validate_coordinates(end_x, end_y)
            
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(self.canvas, start_x, start_y)
            actions.click_and_hold()
            actions.move_to_element_with_offset(self.canvas, end_x, end_y)
            actions.release()
            
            try:
                actions.perform()
                time.sleep(0.5)
            except Exception as e:
                print(f"Warning: Line execution failed: {e}")
    
    def _execute_single_stroke(self, x: int, y: int):
        """Execute a single point stroke"""
        try:
            self.driver.execute_script(f"""
                // Simulate mouse events to create a stroke
                const canvas = document.getElementById('canvas');
                const rect = canvas.getBoundingClientRect();
                const x = {x} + rect.left;
                const y = {y} + rect.top;
                
                // Create and dispatch mouse events
                const mousedownEvent = new MouseEvent('mousedown', {{
                    clientX: x,
                    clientY: y,
                    bubbles: true,
                    cancelable: true
                }});
                
                canvas.dispatchEvent(mousedownEvent);
                
                // Small delay to simulate stroke creation
                setTimeout(() => {{
                    const mouseupEvent = new MouseEvent('mouseup', {{
                        clientX: x,
                        clientY: y,
                        bubbles: true,
                        cancelable: true
                    }});
                    canvas.dispatchEvent(mouseupEvent);
                }}, 100);
            """)
            
            time.sleep(0.3)  # Wait for stroke to complete
            
        except Exception as e:
            print(f"Warning: Single stroke execution failed: {e}")
            # Fallback to Selenium actions if JavaScript fails
            try:
                actions = ActionChains(self.driver)
                actions.move_to_element_with_offset(self.canvas, x, y)
                actions.click_and_hold()
                time.sleep(0.1)
                actions.release()
                actions.perform()
                time.sleep(0.3)
            except Exception as e2:
                print(f"Warning: Fallback stroke execution also failed: {e2}")
    
    def _execute_continuous_stroke(self, points: list):
        """Execute a continuous stroke connecting multiple points"""
        if len(points) < 2:
            print("Warning: Need at least 2 points for continuous stroke")
            return
        
        try:
            # Convert canvas coordinates to screen coordinates
            canvas_rect = self.canvas.rect
            screen_points = []
            for x, y in points:
                screen_x = x + canvas_rect['x']
                screen_y = y + canvas_rect['y']
                screen_points.append((screen_x, screen_y))
            
            # Execute the continuous stroke using JavaScript
            points_json = json.dumps(screen_points)
            self.driver.execute_script(f"""
                // Execute continuous stroke through multiple points
                const canvas = document.getElementById('canvas');
                const points = {points_json};
                
                if (points.length < 2) return;
                
                // Start the stroke
                const startEvent = new MouseEvent('mousedown', {{
                    clientX: points[0][0],
                    clientY: points[0][1],
                    bubbles: true,
                    cancelable: true
                }});
                canvas.dispatchEvent(startEvent);
                
                // Move through intermediate points
                for (let i = 1; i < points.length - 1; i++) {{
                    setTimeout(() => {{
                        const moveEvent = new MouseEvent('mousemove', {{
                            clientX: points[i][0],
                            clientY: points[i][1],
                            bubbles: true,
                            cancelable: true
                        }});
                        canvas.dispatchEvent(moveEvent);
                    }}, i * 50); // 50ms delay between points
                }}
                
                // End the stroke
                setTimeout(() => {{
                    const endEvent = new MouseEvent('mouseup', {{
                        clientX: points[points.length - 1][0],
                        clientY: points[points.length - 1][1],
                        bubbles: true,
                        cancelable: true
                    }});
                    canvas.dispatchEvent(endEvent);
                }}, (points.length - 1) * 50);
            """)
            
            # Wait for the entire stroke to complete
            stroke_duration = len(points) * 0.05 + 0.5  # 50ms per point + 500ms buffer
            time.sleep(stroke_duration)
            
        except Exception as e:
            print(f"Warning: Continuous stroke execution failed: {e}")
            # Fallback to Selenium actions
            try:
                actions = ActionChains(self.driver)
                
                # Move to first point and start stroke
                actions.move_to_element_with_offset(self.canvas, points[0][0], points[0][1])
                actions.click_and_hold()
                
                # Move through intermediate points
                for x, y in points[1:-1]:
                    actions.move_to_element_with_offset(self.canvas, x, y)
                
                # End at last point
                actions.move_to_element_with_offset(self.canvas, points[-1][0], points[-1][1])
                actions.release()
                
                actions.perform()
                time.sleep(0.5)
                
            except Exception as e2:
                print(f"Warning: Fallback continuous stroke execution also failed: {e2}")
    
    def execute_action(self, action: DrawingAction):
        """Execute a complete drawing action"""
        print(f"Executing action: {action.reasoning}")
        
        # Set brush type
        self.set_brush(action.brush)
        
        # Set color
        self.set_color(action.color)
        
        # Execute strokes
        for stroke in action.strokes:
            print(f"  Executing stroke: {stroke.get('description', 'No description')}")
            self.execute_stroke(stroke)
        
        # Wait for all effects to settle
        time.sleep(2)
    
    def capture_canvas(self, filename: str = "current_canvas.png"):
        """Capture the current canvas state as an image"""
        # Get canvas as base64
        canvas_base64 = self.driver.execute_script(
            "return arguments[0].toDataURL('image/png').substring(22);", 
            self.canvas
        )
        
        # Decode and save
        canvas_data = base64.b64decode(canvas_base64)
        with open(filename, "wb") as f:
            f.write(canvas_data)
        
        print(f"Canvas captured as {filename}")
        return filename
    
    def clear_canvas(self):
        """Clear the canvas"""
        clear_button = self.driver.find_element(By.ID, "clearCanvas")
        clear_button.click()
        time.sleep(1)
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

    def _validate_coordinates(self, x: int, y: int) -> tuple:
        """
        Validate and sanitize coordinates to ensure they're within canvas bounds.
        
        Args:
            x: X coordinate
            y: Y coordinate
            
        Returns:
            Tuple of (sanitized_x, sanitized_y)
        """
        try:
            canvas_width = self.canvas.size['width']
            canvas_height = self.canvas.size['height']
        except Exception:
            # Use default safe dimensions if we can't get canvas size
            canvas_width = 800
            canvas_height = 600
        
        # Ensure coordinates are within canvas bounds with a safety margin
        safe_x = max(10, min(x, canvas_width - 10))
        safe_y = max(10, min(y, canvas_height - 10))
        
        return safe_x, safe_y

class AutomatedPainter:
    """
    High-level interface that combines the DrawingAgent with the PaintingBridge
    for automated painting based on text prompts.
    """
    
    def __init__(self, api_key: str, painter_url: str = "file:///path/to/allbrush.html"):
        self.agent = DrawingAgent(api_key)
        self.bridge = PaintingBridge(painter_url)
        
    def start(self):
        """Start the painting interface"""
        self.bridge.start_painting_interface()
    
    def paint_from_prompt(self, prompt: str, canvas_filename: str = "current_canvas.png"):
        """
        Paint based on a text prompt.
        
        Args:
            prompt: Text description of what to paint
            canvas_filename: Filename to save the canvas image
        """
        # Capture current canvas state
        self.bridge.capture_canvas(canvas_filename)
        
        # Generate drawing action
        action = self.agent.analyze_and_plan(prompt, canvas_filename)
        
        # Execute the action
        self.bridge.execute_action(action)
        
        return action
    
    def paint_sequence(self, prompts: list):
        """
        Paint a sequence of elements based on multiple prompts.
        
        Args:
            prompts: List of text prompts to process sequentially
        """
        actions = []
        
        for i, prompt in enumerate(prompts):
            print(f"\n=== Processing Prompt {i+1}/{len(prompts)} ===")
            print(f"Prompt: {prompt}")
            
            action = self.paint_from_prompt(prompt)
            actions.append(action)
            
            print(f"Completed: {action.reasoning}")
        
        return actions
    
    def close(self):
        """Close the painting interface"""
        self.bridge.close()

# Example usage
if __name__ == "__main__":
    # Initialize the automated painter
    painter = AutomatedPainter(
        api_key="your-api-key-here",
        painter_url="file:///path/to/DoodleAgent/allbrush.html"
    )
    
    try:
        # Start the painting interface
        painter.start()
        
        # Define a sequence of prompts for a landscape using various brushes
        landscape_prompts = [
            "Create a warm sunset sky with orange and pink gradients using watercolor",
            "Add dark mountain silhouettes in the background using oil paint",
            "Paint a flowing blue river in the foreground with the flowing brush",
            "Add green trees along the riverbank using crayon for texture",
            "Include some white clouds in the sky with the spray brush",
            "Add fine details with the pen brush for grass and small elements",
            "Use the rainbow brush to add a colorful arc in the sky",
            "Add some playful elements with the wiggle brush"
        ]
        
        # Execute the painting sequence
        actions = painter.paint_sequence(landscape_prompts)
        
        # Save the final result
        painter.bridge.capture_canvas("final_landscape.png")
        print("\nPainting completed! Final result saved as 'final_landscape.png'")
        
    except Exception as e:
        print(f"Error during painting: {e}")
    
    finally:
        painter.close() 