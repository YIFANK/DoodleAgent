from flask import Flask, jsonify, request, render_template_string
import json
import random
import math
import time
import os
from typing import Dict, List, Tuple, Optional
import openai
from config import config

app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Configure OpenAI API key
openai.api_key = app.config['OPENAI_API_KEY']

class RoughDrawingAgent:
    """Simple autonomous drawing agent using Rough.js primitives"""
    
    def __init__(self, canvas_width=800, canvas_height=600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.shapes = []
        self.current_mood = self._pick_mood()
        self.color_palette = self._generate_palette()
        self.composition_state = "starting"  # starting, building, detailing, finishing
        self.shape_count = 0
        self.max_shapes = random.randint(8, 20)
        
    def _pick_mood(self) -> str:
        """Select artistic mood that influences drawing decisions"""
        moods = [
            "geometric", "organic", "chaotic", "minimal", 
            "expressive", "structured", "flowing", "angular"
        ]
        return random.choice(moods)
    
    def _generate_palette(self) -> List[str]:
        """Generate a cohesive color palette"""
        palettes = [
            ["#2c3e50", "#e74c3c", "#f39c12", "#f1c40f"],  # Bold
            ["#34495e", "#95a5a6", "#ecf0f1", "#3498db"],  # Cool
            ["#8e44ad", "#9b59b6", "#e91e63", "#f06292"],  # Purple-Pink
            ["#27ae60", "#2ecc71", "#f39c12", "#e67e22"],  # Nature
            ["#34495e", "#7f8c8d", "#95a5a6", "#bdc3c7"],  # Monochrome
        ]
        return random.choice(palettes)
    
    def _get_canvas_region(self, region: str) -> Tuple[int, int, int, int]:
        """Get coordinates for canvas regions"""
        margin = 50
        regions = {
            "center": (
                self.canvas_width // 4, self.canvas_height // 4,
                self.canvas_width // 2, self.canvas_height // 2
            ),
            "top": (
                margin, margin,
                self.canvas_width - 2*margin, self.canvas_height // 3
            ),
            "bottom": (
                margin, 2*self.canvas_height // 3,
                self.canvas_width - 2*margin, self.canvas_height // 3 - margin
            ),
            "left": (
                margin, margin,
                self.canvas_width // 3, self.canvas_height - 2*margin
            ),
            "right": (
                2*self.canvas_width // 3, margin,
                self.canvas_width // 3 - margin, self.canvas_height - 2*margin
            ),
            "full": (
                margin, margin,
                self.canvas_width - 2*margin, self.canvas_height - 2*margin
            )
        }
        return regions.get(region, regions["center"])
    
    def _create_shape_prompt(self) -> str:
        """Generate creative prompt for LLM based on current state"""
        return f"""You are an autonomous artist creating a {self.current_mood} sketch using Rough.js.

Current state:
- Canvas: {self.canvas_width}x{self.canvas_height}
- Shapes drawn: {self.shape_count}/{self.max_shapes}
- Composition phase: {self.composition_state}
- Available colors: {', '.join(self.color_palette)}
- Artistic mood: {self.current_mood}

Available Rough.js shapes:
- rectangle(x, y, width, height, options)
- circle(x, y, diameter, options)  
- ellipse(x, y, width, height, options)
- line(x1, y1, x2, y2, options)
- polygon(vertices, options) // vertices: [[x1,y1], [x2,y2], ...]
- arc(x, y, width, height, start, stop, closed, options) // angles in radians

Style options include:
- stroke: color, strokeWidth: 1-8
- fill: color, fillStyle: "hachure"|"solid"|"zigzag"|"cross-hatch"|"dots"
- roughness: 0.5-3.0 (sketch intensity)
- bowing: 0-2 (curve amount)

Create ONE shape that feels right for this moment. Consider:
- What would naturally come next?
- How does this relate to the {self.current_mood} mood?
- What story is emerging?

Respond with JSON:
{{
    "shape": "rectangle|circle|ellipse|line|polygon|arc",
    "params": {{
        // shape-specific parameters (x, y, width, etc.)
    }},
    "options": {{
        "stroke": "#color",
        "fill": "#color",
        "fillStyle": "hachure|solid|zigzag|cross-hatch|dots",
        "strokeWidth": number,
        "roughness": number,
        "bowing": number
    }},
    "artistic_reasoning": "Why this shape feels right now"
}}"""

    def _call_llm(self, prompt: str) -> Dict:
        """Get shape decision from LLM"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4.1-nano",
                messages=[
                    {"role": "system", "content": "You are a creative artist. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=500
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"LLM response: {response_text}")
            # Clean JSON formatting
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]
            return json.loads(response_text)
            
        except Exception as e:
            # Fallback to simple shape
            return self._create_fallback_shape()
    
    def _create_fallback_shape(self) -> Dict:
        """Create a simple shape when LLM fails"""
        print("LLM call failed, using fallback shape")
        shapes = ["rectangle", "circle", "ellipse", "line"]
        shape = random.choice(shapes)
        color = random.choice(self.color_palette)
        
        if shape == "rectangle":
            x = random.randint(50, self.canvas_width - 150)
            y = random.randint(50, self.canvas_height - 150)
            w = random.randint(30, 120)
            h = random.randint(30, 120)
            return {
                "shape": "rectangle",
                "params": {"x": x, "y": y, "width": w, "height": h},
                "options": {
                    "stroke": color,
                    "strokeWidth": random.randint(1, 4),
                    "roughness": random.uniform(0.8, 2.0),
                    "bowing": random.uniform(0.2, 1.0)
                },
                "artistic_reasoning": "Intuitive fallback shape"
            }
        elif shape == "circle":
            x = random.randint(80, self.canvas_width - 80)
            y = random.randint(80, self.canvas_height - 80)
            d = random.randint(40, 100)
            return {
                "shape": "circle",
                "params": {"x": x, "y": y, "diameter": d},
                "options": {
                    "stroke": color,
                    "strokeWidth": random.randint(1, 3),
                    "roughness": random.uniform(0.5, 1.5),
                    "bowing": random.uniform(0.1, 0.8)
                },
                "artistic_reasoning": "Organic circular form"
            }
        elif shape == "line":
            x1 = random.randint(50, self.canvas_width - 50)
            y1 = random.randint(50, self.canvas_height - 50)
            x2 = x1 + random.randint(-100, 100)
            y2 = y1 + random.randint(-100, 100)
            return {
                "shape": "line",
                "params": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "options": {
                    "stroke": color,
                    "strokeWidth": random.randint(1, 5),
                    "roughness": random.uniform(0.8, 2.5),
                    "bowing": random.uniform(0.3, 1.2)
                },
                "artistic_reasoning": "Expressive line gesture"
            }
        else:  # ellipse
            x = random.randint(70, self.canvas_width - 70)
            y = random.randint(70, self.canvas_height - 70)
            w = random.randint(40, 120)
            h = random.randint(30, 80)
            return {
                "shape": "ellipse",
                "params": {"x": x, "y": y, "width": w, "height": h},
                "options": {
                    "stroke": color,
                    "strokeWidth": random.randint(1, 3),
                    "roughness": random.uniform(0.6, 1.8),
                    "bowing": random.uniform(0.2, 1.0)
                },
                "artistic_reasoning": "Flowing elliptical form"
            }
    
    def _validate_shape(self, shape_data: Dict) -> bool:
        """Validate shape data before adding"""
        if "shape" not in shape_data or "params" not in shape_data:
            return False
            
        shape_type = shape_data["shape"]
        params = shape_data["params"]
        
        # Basic boundary checking
        if shape_type == "rectangle":
            x, y = params.get("x", 0), params.get("y", 0)
            w, h = params.get("width", 0), params.get("height", 0)
            return (0 <= x <= self.canvas_width and 0 <= y <= self.canvas_height and
                    w > 0 and h > 0 and x + w <= self.canvas_width and y + h <= self.canvas_height)
                    
        elif shape_type == "circle":
            x, y = params.get("x", 0), params.get("y", 0)
            d = params.get("diameter", 0)
            r = d / 2
            return (r <= x <= self.canvas_width - r and r <= y <= self.canvas_height - r and d > 0)
            
        elif shape_type == "line":
            x1, y1 = params.get("x1", 0), params.get("y1", 0)
            x2, y2 = params.get("x2", 0), params.get("y2", 0)
            return (0 <= x1 <= self.canvas_width and 0 <= y1 <= self.canvas_height and
                    0 <= x2 <= self.canvas_width and 0 <= y2 <= self.canvas_height)
                    
        # Add more validation for other shapes as needed
        return True
    
    def _update_composition_state(self):
        """Update the composition phase based on progress"""
        progress = self.shape_count / self.max_shapes
        
        if progress < 0.3:
            self.composition_state = "starting"
        elif progress < 0.6:
            self.composition_state = "building"
        elif progress < 0.85:
            self.composition_state = "detailing"
        else:
            self.composition_state = "finishing"
    
    def create_drawing(self, test_mode=False) -> Dict:
        """Main method to create autonomous sketch"""
        drawing_session = {
            "shapes": [],
            "metadata": {
                "mood": self.current_mood,
                "palette": self.color_palette,
                "canvas_size": {"width": self.canvas_width, "height": self.canvas_height},
                "session_id": int(time.time()),
                "total_shapes": 0,
                "completion_reason": None
            }
        }
        
        for iteration in range(self.max_shapes):
            # Update composition state
            self._update_composition_state()
            
            if test_mode:
                # Use fallback shapes for testing without OpenAI
                shape_data = self._create_fallback_shape()
            else:
                # Generate shape prompt and get LLM decision
                prompt = self._create_shape_prompt()
                shape_data = self._call_llm(prompt)
            
            # Validate and add shape
            if self._validate_shape(shape_data):
                self.shapes.append(shape_data)
                drawing_session["shapes"].append(shape_data)
                self.shape_count += 1
                
                # Small delay for natural pacing
                time.sleep(0.1)
            else:
                # Use fallback if validation fails
                fallback = self._create_fallback_shape()
                self.shapes.append(fallback)
                drawing_session["shapes"].append(fallback)
                self.shape_count += 1
        
        drawing_session["metadata"]["total_shapes"] = len(drawing_session["shapes"])
        drawing_session["metadata"]["completion_reason"] = f"Completed {self.current_mood} composition"
        
        return drawing_session

@app.route('/api/generate', methods=['POST'])
def generate_drawing():
    """API endpoint for autonomous drawing generation"""
    try:
        data = request.get_json() or {}
        canvas_width = data.get('canvas_width', 800)
        canvas_height = data.get('canvas_height', 600)
        
        # Validate OpenAI API key
        if not openai.api_key or openai.api_key == "your-api-key-here":
            return jsonify({
                "success": False,
                "error": "OpenAI API key not configured",
                "message": "Please set OPENAI_API_KEY in your .env file"
            }), 400
        
        # Check if we should use test mode (no OpenAI)
        test_mode = data.get('test_mode', False) or not openai.api_key or openai.api_key == "your-api-key-here"
        
        # Create and run autonomous agent
        agent = RoughDrawingAgent(canvas_width, canvas_height)
        drawing_session = agent.create_drawing(test_mode=test_mode)
        
        mode_message = " (test mode - using fallback shapes)" if test_mode else ""
        
        return jsonify({
            "success": True,
            "drawing": drawing_session,
            "message": f"Created {drawing_session['metadata']['mood']} drawing with {drawing_session['metadata']['total_shapes']} shapes{mode_message}"
        })
        
    except Exception as e:
        # Log the full error for debugging
        print(f"Error in generate_drawing: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate drawing"
        }), 500

@app.route('/api/test', methods=['GET'])
def test_api():
    """Simple test endpoint to verify API is working"""
    return jsonify({
        "success": True,
        "message": "API is working",
        "openai_configured": bool(openai.api_key and openai.api_key != "your-api-key-here"),
        "config_loaded": bool(app.config.get('OPENAI_API_KEY'))
    })

@app.route('/favicon.ico')
def favicon():
    """Return a simple favicon to avoid 404s"""
    return '', 204  # No content

@app.route('/', methods=['GET'])
@app.route('/api/demo', methods=['GET'])
def demo_page():
    """Demo page to visualize the drawings"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Autonomous Rough.js Drawing Agent</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎨</text></svg>">
    <script src="https://unpkg.com/roughjs@4.5.2/bundled/rough.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        canvas { 
            border: 2px solid #ddd; 
            background: white; 
            margin: 10px 0; 
            border-radius: 4px; 
        }
        button { 
            background: #3498db; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 4px; 
            cursor: pointer; 
            margin: 5px; 
        }
        button:hover { background: #2980b9; }
        .info { 
            background: #ecf0f1; 
            padding: 15px; 
            border-radius: 4px; 
            margin: 10px 0; 
        }
        .status { 
            padding: 10px; 
            margin: 10px 0; 
            border-radius: 4px; 
        }
        .success { background: #d5edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Autonomous Rough.js Drawing Agent</h1>
        <p>Watch an AI create expressive, hand-drawn sketches using different artistic moods and styles.</p>
        
        <div>
            <button onclick="generateDrawing()">Generate New Drawing</button>
            <button onclick="clearCanvas()">Clear Canvas</button>
            <button onclick="testAPI()">Test API</button>
        </div>
        
        <div id="status"></div>
        <div id="info" class="info" style="display:none;"></div>
        
        <canvas id="drawingCanvas" width="800" height="600"></canvas>
    </div>

    <script>
        let canvas = document.getElementById('drawingCanvas');
        let rc, ctx;
        
        // Initialize Rough.js when page loads
        window.addEventListener('load', function() {
            if (typeof rough !== 'undefined') {
                rc = rough.canvas(canvas);
                ctx = canvas.getContext('2d');
                showStatus('Ready to draw!', false);
            } else {
                showStatus('Error: Rough.js failed to load', true);
            }
        });

        function showStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + (isError ? 'error' : 'success');
        }

        function showInfo(data) {
            const info = document.getElementById('info');
            const metadata = data.metadata;
            info.innerHTML = `
                <strong>Drawing Info:</strong><br>
                Mood: ${metadata.mood}<br>
                Shapes: ${metadata.total_shapes}<br>
                Palette: ${metadata.palette.join(', ')}<br>
                Completion: ${metadata.completion_reason}
            `;
            info.style.display = 'block';
        }

        function clearCanvas() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            document.getElementById('info').style.display = 'none';
        }

        function drawShape(shape) {
            if (!rc) {
                console.error('Rough.js not initialized');
                return;
            }
            
            const { shape: shapeType, params, options } = shape;
            
            try {
                switch(shapeType) {
                    case 'rectangle':
                        rc.rectangle(params.x, params.y, params.width, params.height, options);
                        break;
                    case 'circle':
                        rc.circle(params.x, params.y, params.diameter, options);
                        break;
                    case 'ellipse':
                        rc.ellipse(params.x, params.y, params.width, params.height, options);
                        break;
                    case 'line':
                        rc.line(params.x1, params.y1, params.x2, params.y2, options);
                        break;
                    case 'polygon':
                        rc.polygon(params.vertices, options);
                        break;
                    case 'arc':
                        rc.arc(params.x, params.y, params.width, params.height, 
                               params.start, params.stop, params.closed, options);
                        break;
                }
            } catch(e) {
                console.warn('Failed to draw shape:', shapeType, e);
            }
        }

        async function generateDrawing() {
            if (!rc) {
                showStatus('Rough.js not ready yet, please wait...', true);
                return;
            }
            
            showStatus('Generating drawing...', false);
            clearCanvas();
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        canvas_width: canvas.width,
                        canvas_height: canvas.height,
                        test_mode: false  // Set to true to test without OpenAI
                    })
                });
                
                // Check if response is JSON
                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const text = await response.text();
                    console.error('Non-JSON response:', text.substring(0, 200));
                    showStatus('Server error: Expected JSON, got HTML. Check server logs.', true);
                    return;
                }
                
                const data = await response.json();
                
                if (data.success) {
                    showStatus(data.message, false);
                    showInfo(data.drawing);
                    
                    // Draw shapes with slight delay for visual effect
                    for (let i = 0; i < data.drawing.shapes.length; i++) {
                        setTimeout(() => {
                            drawShape(data.drawing.shapes[i]);
                        }, i * 200);
                    }
                } else {
                    showStatus('Error: ' + data.message, true);
                    console.error('API Error:', data);
                }
            } catch (error) {
                console.error('Full error:', error);
                showStatus('Network error: ' + error.message, true);
            }
        }

        // Add test function
        async function testAPI() {
            try {
                const response = await fetch('/api/test');
                const data = await response.json();
                console.log('API Test:', data);
                showStatus(`API Test: ${data.message} | OpenAI: ${data.openai_configured}`, false);
            } catch (error) {
                console.error('Test failed:', error);
                showStatus('API test failed: ' + error.message, true);
            }
        }

        // Don't auto-generate on load, wait for user click or page ready
        // generateDrawing();
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(debug=True, port=5001)