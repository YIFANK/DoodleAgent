#!/usr/bin/env python3
"""
Automated Painting Tool Controller
Automates the dli-paint web application using browser automation
"""

import time
import json
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import numpy as np
from PIL import Image
import io


@dataclass
class Point:
    x: float
    y: float


@dataclass
class BrushConfig:
    size: float = 10.0
    opacity: float = 1.0
    color: Tuple[int, int, int] = (0, 0, 0)  # RGB
    pressure: float = 1.0
    bristleCount: int = 50  # Number of bristles (10-100)


@dataclass
class DrawingCommand:
    """Represents a single drawing operation"""
    command_type: str  # 'stroke', 'dot', 'line', 'curve'
    points: List[Point]
    brush_config: BrushConfig
    duration: float = 1.0  # seconds to complete the action


class PaintAutomator:
    """Main class for automating the painting interface"""
    
    def __init__(self, headless: bool = False, canvas_size: Tuple[int, int] = (800, 600)):
        self.headless = headless
        self.canvas_size = canvas_size
        self.driver = None
        self.canvas_element = None
        self.canvas_bounds = None
        
    def start_browser(self, url: str = "http://localhost:8000"):
        """Initialize the browser and navigate to the painting app"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-web-security")  # Allow local file access
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_window_size(*self.canvas_size)
        self.driver.get(url)
        
        # Wait for the canvas to load
        self.canvas_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
        
        # Get canvas bounds for coordinate conversion
        self.canvas_bounds = self.canvas_element.rect
        print(f"Canvas bounds: {self.canvas_bounds}")
        
        # Get actual canvas size from JavaScript
        canvas_info = self.driver.execute_script("""
            var canvas = document.querySelector('canvas');
            return {
                width: canvas.width,
                height: canvas.height,
                clientWidth: canvas.clientWidth,
                clientHeight: canvas.clientHeight,
                offsetWidth: canvas.offsetWidth,
                offsetHeight: canvas.offsetHeight,
                rect: canvas.getBoundingClientRect()
            };
        """)
        print(f"Canvas info: {canvas_info}")
        
        self.actual_canvas_width = canvas_info['width']
        self.actual_canvas_height = canvas_info['height']
        
    def close_browser(self):
        """Clean up browser resources"""
        if self.driver:
            self.driver.quit()
            
    def set_brush_config(self, config: BrushConfig):
        """Configure brush settings using JavaScript API"""
        if hasattr(config, 'size'):
            self.set_brush_size_js(config.size)
        
        if hasattr(config, 'color') and config.color:
            self.set_brush_color_rgb_js(config.color, config.opacity)
        
        if hasattr(config, 'bristleCount'):
            self.set_bristle_count_js(config.bristleCount)
        
        return True
    
    def inject_paint_api(self):
        """Inject a comprehensive API for controlling the paint application"""
        js_code = """
        // Wait for Paint object to be available
        function waitForPaint(callback) {
            if (window.paint) {
                callback();
            } else {
                setTimeout(() => waitForPaint(callback), 100);
            }
        }
        
        waitForPaint(() => {
            // Create comprehensive automation API
            window.paintAPI = {
                // Brush size control
                setBrushSize: function(size) {
                    size = Math.max(5, Math.min(75, size)); // Clamp to valid range
                    window.paint.brushScale = size;
                    if (window.paint.brushSizeSlider) {
                        window.paint.brushSizeSlider.setValue(size);
                    }
                    return true;
                },
                
                getBrushSize: function() {
                    return window.paint.brushScale;
                },
                
                // Brush color control (HSVA format)
                setBrushColor: function(h, s, v, a) {
                    if (typeof h === 'object') {
                        // Accept {h, s, v, a} object or [h, s, v, a] array
                        const color = Array.isArray(h) ? h : [h.h, h.s, h.v, h.a];
                        window.paint.brushColorHSVA = color;
                    } else {
                        window.paint.brushColorHSVA = [h || 0, s || 1, v || 1, a || 0.8];
                    }
                    window.paint.needsRedraw = true;
                    return true;
                },
                
                setBrushColorRGB: function(r, g, b, a) {
                    // Convert RGB to HSV (simplified conversion)
                    const max = Math.max(r, g, b);
                    const min = Math.min(r, g, b);
                    const diff = max - min;
                    
                    let h = 0;
                    if (diff !== 0) {
                        if (max === r) h = ((g - b) / diff) % 6;
                        else if (max === g) h = (b - r) / diff + 2;
                        else h = (r - g) / diff + 4;
                        h /= 6;
                    }
                    
                    const s = max === 0 ? 0 : diff / max;
                    const v = max;
                    
                    this.setBrushColor(h, s, v, a || 0.8);
                    return true;
                },
                
                getBrushColor: function() {
                    return {
                        h: window.paint.brushColorHSVA[0],
                        s: window.paint.brushColorHSVA[1],
                        v: window.paint.brushColorHSVA[2],
                        a: window.paint.brushColorHSVA[3]
                    };
                },
                
                // Bristle count control
                setBristleCount: function(count) {
                    count = Math.max(10, Math.min(100, Math.floor(count)));
                    if (window.paint.brush) {
                        window.paint.brush.setBristleCount(count);
                    }
                    return true;
                },
                
                getBristleCount: function() {
                    return window.paint.brush ? window.paint.brush.bristleCount : 0;
                },
                
                // Painting control
                startPainting: function(x, y) {
                    // Convert screen coordinates to canvas coordinates
                    const rect = window.paint.canvas.getBoundingClientRect();
                    const canvasX = x;
                    const canvasY = window.paint.canvas.height - y; // Flip Y coordinate
                    
                    // Update brush position
                    window.paint.brushX = canvasX;
                    window.paint.brushY = canvasY;
                    
                    // Initialize brush if needed
                    if (!window.paint.brushInitialized) {
                        window.paint.brush.initialize(canvasX, canvasY, 2.0 * window.paint.brushScale, window.paint.brushScale);
                        window.paint.brushInitialized = true;
                    }
                    
                    // Start painting mode
                    window.paint.interactionState = 1; // InteractionMode.PAINTING
                    window.paint.saveSnapshot();
                    
                    return true;
                },
                
                continuePainting: function(x, y) {
                    if (window.paint.interactionState !== 1) return false; // Not painting
                    
                    const canvasX = x;
                    const canvasY = window.paint.canvas.height - y;
                    
                    // Update brush position
                    window.paint.brushX = canvasX;
                    window.paint.brushY = canvasY;
                    
                    return true;
                },
                
                stopPainting: function() {
                    window.paint.interactionState = 0; // InteractionMode.NONE
                    return true;
                },
                
                // Draw complete stroke
                drawStroke: function(points, options = {}) {
                    if (!points || points.length === 0) return false;
                    
                    // Apply options
                    if (options.brushSize) this.setBrushSize(options.brushSize);
                    if (options.color) {
                        if (Array.isArray(options.color)) {
                            this.setBrushColor(...options.color);
                        } else {
                            this.setBrushColor(options.color);
                        }
                    }
                    if (options.bristleCount) this.setBristleCount(options.bristleCount);
                    
                    // Start painting at first point
                    this.startPainting(points[0].x, points[0].y);
                    
                    // Draw through all points with small delays
                    points.slice(1).forEach((point, index) => {
                        setTimeout(() => {
                            this.continuePainting(point.x, point.y);
                        }, (index + 1) * 16); // ~60 FPS
                    });
                    
                    // Stop painting after all points
                    setTimeout(() => {
                        this.stopPainting();
                    }, points.length * 16);
                    
                    return true;
                },
                
                // Canvas control
                clearCanvas: function() {
                    window.paint.clear();
                    return true;
                },
                
                saveCanvas: function() {
                    window.paint.save();
                    return true;
                },
                
                // Undo/Redo
                undo: function() {
                    window.paint.undo();
                    return true;
                },
                
                redo: function() {
                    window.paint.redo();
                    return true;
                },
                
                // Canvas positioning
                panCanvas: function(deltaX, deltaY) {
                    window.paint.paintingRectangle.left += deltaX;
                    window.paint.paintingRectangle.bottom += deltaY;
                    
                    // Clamp to valid bounds
                    window.paint.paintingRectangle.left = Math.max(-window.paint.paintingRectangle.width, 
                        Math.min(window.paint.canvas.width, window.paint.paintingRectangle.left));
                    window.paint.paintingRectangle.bottom = Math.max(-window.paint.paintingRectangle.height, 
                        Math.min(window.paint.canvas.height, window.paint.paintingRectangle.bottom));
                    
                    window.paint.needsRedraw = true;
                    return true;
                },
                
                // Get application state
                getState: function() {
                    return {
                        brushSize: this.getBrushSize(),
                        brushColor: this.getBrushColor(),
                        bristleCount: this.getBristleCount(),
                        canvasRect: {
                            left: window.paint.paintingRectangle.left,
                            bottom: window.paint.paintingRectangle.bottom,
                            width: window.paint.paintingRectangle.width,
                            height: window.paint.paintingRectangle.height
                        },
                        isPainting: window.paint.interactionState === 1,
                        canUndo: window.paint.canUndo(),
                        canRedo: window.paint.canRedo()
                    };
                },
                
                // Wait for application to be ready
                waitReady: function() {
                    return window.paint && window.paint.brush && window.paint.brushInitialized;
                }
            };
            
            console.log('Paint API injected successfully');
            console.log('Available methods:', Object.keys(window.paintAPI));
        });
        """
        
        return self.driver.execute_script(js_code)

    def wait_for_paint_ready(self, timeout=10):
        """Wait for the paint application to be fully loaded and ready"""
        js_code = """
        return window.paintAPI && window.paintAPI.waitReady();
        """
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if self.driver.execute_script(js_code):
                    return True
            except:
                pass
            time.sleep(0.1)
        
        return False

    def set_brush_size_js(self, size: float):
        """Set brush size using JavaScript API"""
        js_code = f"return window.paintAPI ? window.paintAPI.setBrushSize({size}) : false;"
        return self.driver.execute_script(js_code)

    def set_brush_color_js(self, color: Tuple[float, float, float, float]):
        """Set brush color using JavaScript API (HSVA format)"""
        h, s, v, a = color
        js_code = f"return window.paintAPI ? window.paintAPI.setBrushColor({h}, {s}, {v}, {a}) : false;"
        return self.driver.execute_script(js_code)

    def set_brush_color_rgb_js(self, color: Tuple[int, int, int], alpha: float = 0.8):
        """Set brush color using RGB values"""
        r, g, b = [c / 255.0 for c in color]  # Normalize to 0-1 range
        js_code = f"return window.paintAPI ? window.paintAPI.setBrushColorRGB({r}, {g}, {b}, {alpha}) : false;"
        return self.driver.execute_script(js_code)

    def set_bristle_count_js(self, count: int):
        """Set bristle count using JavaScript API"""
        js_code = f"return window.paintAPI ? window.paintAPI.setBristleCount({count}) : false;"
        return self.driver.execute_script(js_code)

    def draw_stroke_js(self, points: List[Point], brush_config: BrushConfig = None):
        """Draw a complete stroke using JavaScript API"""
        points_data = [{"x": p.x, "y": p.y} for p in points]
        
        options = {}
        if brush_config:
            options['brushSize'] = brush_config.size
            if hasattr(brush_config, 'bristleCount'):
                options['bristleCount'] = brush_config.bristleCount
            # Convert RGB to normalized values for color
            if brush_config.color:
                r, g, b = [c / 255.0 for c in brush_config.color]
                options['color'] = [r, g, b, brush_config.opacity]
        
        js_code = f"""
        if (window.paintAPI) {{
            return window.paintAPI.drawStroke({json.dumps(points_data)}, {json.dumps(options)});
        }}
        return false;
        """
        
        return self.driver.execute_script(js_code)

    def clear_canvas_js(self):
        """Clear the canvas using JavaScript API"""
        js_code = "return window.paintAPI ? window.paintAPI.clearCanvas() : false;"
        return self.driver.execute_script(js_code)

    def get_paint_state(self):
        """Get current state of the paint application"""
        js_code = "return window.paintAPI ? window.paintAPI.getState() : null;"
        return self.driver.execute_script(js_code)
        
    def screen_to_canvas_coords(self, screen_x: float, screen_y: float) -> Tuple[float, float]:
        """Convert screen coordinates to canvas coordinates with bounds checking"""
        # For JavaScript API, we use screen coordinates directly
        # For Selenium, we need to convert to element-relative coordinates
        canvas_x = screen_x - self.canvas_bounds['x']
        canvas_y = screen_y - self.canvas_bounds['y']
        
        # Clamp to canvas bounds to prevent "move target out of bounds" error
        canvas_x = max(0, min(canvas_x, self.canvas_bounds['width'] - 1))
        canvas_y = max(0, min(canvas_y, self.canvas_bounds['height'] - 1))
        
        return canvas_x, canvas_y
    
    def get_safe_coordinates(self, points: List[Point]) -> List[Point]:
        """Ensure all points are within safe canvas bounds"""
        if not hasattr(self, 'actual_canvas_width'):
            # Fallback to canvas bounds
            max_x = self.canvas_bounds['width'] - 50  # Leave some margin
            max_y = self.canvas_bounds['height'] - 50
        else:
            max_x = self.actual_canvas_width - 50
            max_y = self.actual_canvas_height - 50
        
        safe_points = []
        for point in points:
            safe_x = max(50, min(point.x, max_x))  # 50px margin on all sides
            safe_y = max(50, min(point.y, max_y))
            safe_points.append(Point(safe_x, safe_y))
        
        return safe_points
        
    def draw_stroke(self, points: List[Point], brush_config: BrushConfig):
        """Draw a continuous stroke using JavaScript API (preferred) or mouse simulation"""
        if not points:
            return
        
        # Get safe coordinates
        safe_points = self.get_safe_coordinates(points)
        
        # Try JavaScript API first (much faster and more reliable)
        try:
            success = self.draw_stroke_js(safe_points, brush_config)
            if success:
                print(f"Drew stroke with {len(safe_points)} points using JavaScript API")
                return
        except Exception as e:
            print(f"JavaScript API failed, falling back to mouse simulation: {e}")
        
        # Fallback to mouse simulation with safe coordinates
        self.set_brush_config(brush_config)
        
        print(f"Drawing stroke with mouse simulation: {len(safe_points)} points")
        print(f"Canvas bounds: {self.canvas_bounds}")
        print(f"First point: {safe_points[0]}, Last point: {safe_points[-1]}")
        
        try:
            # Move to first point
            start_point = safe_points[0]
            canvas_x, canvas_y = self.screen_to_canvas_coords(start_point.x, start_point.y)
            
            print(f"Moving to canvas coordinates: ({canvas_x}, {canvas_y})")
            
            actions = ActionChains(self.driver)
            actions.move_to_element_with_offset(self.canvas_element, canvas_x, canvas_y)
            actions.perform()
            
            # Start painting with mouse down
            actions = ActionChains(self.driver)
            actions.click_and_hold(self.canvas_element)
            actions.perform()
            
            # Draw through all points with small delays for smooth strokes
            for i, point in enumerate(safe_points[1:], 1):
                canvas_x, canvas_y = self.screen_to_canvas_coords(point.x, point.y)
                
                if i % 10 == 0:  # Debug every 10th point
                    print(f"Point {i}: screen({point.x}, {point.y}) -> canvas({canvas_x}, {canvas_y})")
                
                actions = ActionChains(self.driver)
                actions.move_to_element_with_offset(self.canvas_element, canvas_x, canvas_y)
                actions.perform()
                time.sleep(0.02)  # Small delay for smooth painting
            
            # Release mouse to stop painting
            actions = ActionChains(self.driver)
            actions.release()
            actions.perform()
            
            print("Stroke completed successfully")
            
        except Exception as e:
            print(f"Mouse simulation failed: {e}")
            import traceback
            traceback.print_exc()
        
    def draw_circle(self, center: Point, radius: float, brush_config: BrushConfig, segments: int = 32):
        """Draw a circle by creating a stroke with multiple points"""
        points = []
        for i in range(segments + 1):
            angle = 2 * np.pi * i / segments
            x = center.x + radius * np.cos(angle)
            y = center.y + radius * np.sin(angle)
            points.append(Point(x, y))
        
        self.draw_stroke(points, brush_config)
        
    def draw_line(self, start: Point, end: Point, brush_config: BrushConfig):
        """Draw a straight line"""
        self.draw_stroke([start, end], brush_config)
        
    def execute_drawing_sequence(self, commands: List[DrawingCommand]):
        """Execute a sequence of drawing commands"""
        for command in commands:
            if command.command_type == 'stroke':
                self.draw_stroke(command.points, command.brush_config)
            elif command.command_type == 'line':
                if len(command.points) >= 2:
                    self.draw_line(command.points[0], command.points[1], command.brush_config)
            elif command.command_type == 'dot':
                if command.points:
                    self.draw_stroke([command.points[0]], command.brush_config)
            elif command.command_type == 'circle':
                if len(command.points) >= 2:
                    center = command.points[0]
                    radius_point = command.points[1]
                    radius = np.sqrt((center.x - radius_point.x)**2 + (center.y - radius_point.y)**2)
                    self.draw_circle(center, radius, command.brush_config)
                    
            time.sleep(command.duration)
            
    def capture_canvas(self) -> Image.Image:
        """Capture the current canvas as an image"""
        # Take screenshot of the canvas element
        canvas_screenshot = self.canvas_element.screenshot_as_png
        return Image.open(io.BytesIO(canvas_screenshot))
        
    def save_canvas(self, filename: str):
        """Save the current canvas to a file"""
        canvas_image = self.capture_canvas()
        canvas_image.save(filename)
        
    def pan_canvas(self, start_point: Point, end_point: Point):
        """Pan the canvas using Space + drag"""
        actions = ActionChains(self.driver)
        
        # Hold space key down
        actions.key_down(' ')
        
        # Move to start point and drag to end point
        canvas_start_x, canvas_start_y = self.screen_to_canvas_coords(start_point.x, start_point.y)
        canvas_end_x, canvas_end_y = self.screen_to_canvas_coords(end_point.x, end_point.y)
        
        actions.move_to_element_with_offset(self.canvas_element, canvas_start_x, canvas_start_y)
        actions.click_and_hold()
        actions.move_to_element_with_offset(self.canvas_element, canvas_end_x, canvas_end_y)
        actions.release()
        
        # Release space key
        actions.key_up(' ')
        actions.perform()
        
    def resize_canvas(self, new_width: int, new_height: int):
        """Resize canvas by dragging edges"""
        # This would need to identify the resize handles on the canvas edges
        # Implementation depends on how the resize mechanism works in the app
        # Likely involves finding edge elements and dragging them
        pass


class DrawingProgrammer:
    """Helper class for creating drawing programs"""
    
    @staticmethod
    def create_spiral(center: Point, max_radius: float, turns: int = 3, points_per_turn: int = 20) -> List[Point]:
        """Generate points for a spiral pattern"""
        points = []
        total_points = turns * points_per_turn
        
        for i in range(total_points):
            angle = 2 * np.pi * turns * i / total_points
            radius = max_radius * i / total_points
            x = center.x + radius * np.cos(angle)
            y = center.y + radius * np.sin(angle)
            points.append(Point(x, y))
            
        return points
        
    @staticmethod
    def create_wave(start: Point, end: Point, amplitude: float, frequency: int = 3, points: int = 50) -> List[Point]:
        """Generate points for a wave pattern"""
        wave_points = []
        
        for i in range(points):
            t = i / (points - 1)
            x = start.x + t * (end.x - start.x)
            y = start.y + t * (end.y - start.y) + amplitude * np.sin(2 * np.pi * frequency * t)
            wave_points.append(Point(x, y))
            
        return wave_points


def main():
    """Example usage of the painting automation"""
    
    # Initialize the automator
    painter = PaintAutomator(headless=False)
    
    try:
        # Start the browser and load the painting app
        painter.start_browser("http://localhost:8000")
        time.sleep(3)  # Wait for app to fully load
        
        # Get window and canvas dimensions for debugging
        window_size = painter.driver.get_window_size()
        print(f"Browser window size: {window_size}")
        
        # Inject JavaScript API
        print("Injecting Paint API...")
        painter.inject_paint_api()
        
        # Wait for paint application to be ready
        print("Waiting for paint application to initialize...")
        if not painter.wait_for_paint_ready(timeout=15):
            print("Warning: Paint application may not be fully ready")
        
        # Get canvas dimensions and painting area
        paint_info = painter.driver.execute_script("""
            if (window.paint) {
                return {
                    canvasWidth: window.paint.canvas.width,
                    canvasHeight: window.paint.canvas.height,
                    paintingRect: {
                        left: window.paint.paintingRectangle.left,
                        bottom: window.paint.paintingRectangle.bottom,
                        width: window.paint.paintingRectangle.width,
                        height: window.paint.paintingRectangle.height
                    }
                };
            }
            return null;
        """)
        print(f"Paint app info: {paint_info}")
        
        # Calculate safe drawing area
        if paint_info and paint_info['paintingRect']:
            rect = paint_info['paintingRect']
            safe_left = rect['left'] + 50
            safe_bottom = rect['bottom'] + 50
            safe_width = rect['width'] - 100
            safe_height = rect['height'] - 100
            
            print(f"Safe drawing area: ({safe_left}, {safe_bottom}) size: {safe_width}x{safe_height}")
        else:
            # Use conservative defaults
            safe_left, safe_bottom = 150, 150
            safe_width, safe_height = 400, 300
            print(f"Using default safe area: ({safe_left}, {safe_bottom}) size: {safe_width}x{safe_height}")
        
        # Define brush configurations with bristle counts
        small_brush = BrushConfig(size=15.0, color=(50, 50, 200), opacity=0.8, bristleCount=25)
        medium_brush = BrushConfig(size=30.0, color=(200, 50, 50), opacity=0.6, bristleCount=60)
        large_brush = BrushConfig(size=50.0, color=(50, 200, 50), opacity=0.4, bristleCount=85)
        
        # Test current state
        state = painter.get_paint_state()
        print(f"Initial state: {state}")
        
        # Create drawing commands with safe coordinates
        commands = []
        
        # Draw a small spiral
        spiral_center = Point(safe_left + safe_width * 0.3, safe_bottom + safe_height * 0.3)
        spiral_points = DrawingProgrammer.create_spiral(
            spiral_center, max_radius=min(safe_width, safe_height) * 0.15, turns=2
        )
        commands.append(DrawingCommand('stroke', spiral_points, small_brush, 2.0))
        
        # Draw a wave
        wave_start = Point(safe_left + safe_width * 0.1, safe_bottom + safe_height * 0.7)
        wave_end = Point(safe_left + safe_width * 0.9, safe_bottom + safe_height * 0.7)
        wave_points = DrawingProgrammer.create_wave(
            wave_start, wave_end, amplitude=safe_height * 0.1, frequency=2
        )
        commands.append(DrawingCommand('stroke', wave_points, medium_brush, 2.5))
        
        # Draw a circle
        circle_center = Point(safe_left + safe_width * 0.7, safe_bottom + safe_height * 0.3)
        circle_radius = min(safe_width, safe_height) * 0.12
        circle_points = []
        for i in range(33):  # 32 segments + close the circle
            angle = 2 * np.pi * i / 32
            x = circle_center.x + circle_radius * np.cos(angle)
            y = circle_center.y + circle_radius * np.sin(angle)
            circle_points.append(Point(x, y))
        commands.append(DrawingCommand('stroke', circle_points, large_brush, 1.5))
        
        # Execute the drawing sequence
        print("Starting automated painting...")
        painter.execute_drawing_sequence(commands)
        
        # Test JavaScript controls with safe coordinates
        print("Testing direct JavaScript controls...")
        painter.set_brush_size_js(25)
        painter.set_brush_color_rgb_js((255, 165, 0), 0.7)  # Orange
        
        # Draw a simple line using JS API in safe area
        simple_line = [
            Point(safe_left + 50, safe_bottom + 50), 
            Point(safe_left + 150, safe_bottom + 100)
        ]
        painter.draw_stroke_js(simple_line, BrushConfig(size=20, color=(255, 165, 0), bristleCount=40))
        
        # Get final state
        final_state = painter.get_paint_state()
        print(f"Final state: {final_state}")
        
        # Save the result
        time.sleep(2)  # Wait for rendering to complete
        painter.save_canvas("automated_painting.png")
        print("Painting saved as automated_painting.png")
        
        # Keep browser open for inspection
        input("Press Enter to close...")
        
    except Exception as e:
        print(f"Error during automation: {e}")
        import traceback
        traceback.print_exc()
        
        # Debug information
        try:
            print("\nDebug information:")
            print(f"Canvas bounds: {painter.canvas_bounds}")
            if hasattr(painter, 'actual_canvas_width'):
                print(f"Actual canvas size: {painter.actual_canvas_width}x{painter.actual_canvas_height}")
            
            window_size = painter.driver.get_window_size()
            print(f"Window size: {window_size}")
            
        except Exception as debug_e:
            print(f"Could not get debug info: {debug_e}")
        
    finally:
        painter.close_browser()


if __name__ == "__main__":
    main()