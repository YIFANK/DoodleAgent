from flask import Flask, jsonify, request, render_template_string
import json
import random
import math
import time
import os
import base64
from typing import Dict, List, Tuple, Optional
import openai
from config import config
import datetime
from PIL import Image
import io
import base64

app = Flask(__name__)

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Configure OpenAI API key
openai.api_key = app.config['OPENAI_API_KEY']

# Create output directories
OUTPUT_DIR = "illustrations"
CANVAS_DIR = os.path.join(OUTPUT_DIR, "canvas_states")
for directory in [OUTPUT_DIR, CANVAS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"📁 Created directory: {directory}")

class RoughDrawingAgent:
    """Autonomous drawing agent that creates shapes based on current canvas state"""

    def __init__(self, canvas_width=800, canvas_height=600):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.shapes = []
        self.current_mood = None
        self.color_palette = []
        self.palette_reasoning = ""
        self.composition_state = "starting"
        self.shape_count = 0
        self.max_shapes = 8
        self.session_id = int(time.time())

    # def _create_mood_prompt(self) -> str:
    #     """Generate prompt for LLM to choose artistic mood"""
    #     return "You are an creative, expressive, opinionated artist about to create a doodle that noone has seen. Summarize it with one evocative word (example: threshold, echo, becoming)"
    #     # return """You are an creative, expressive, opinionated artist about to create a doodle that noone has seen before.
    #     # Describe this doodle in a sentence"""
    #     # return "You are an creative artist that likes to doodle. Generate an animal or object that you want to sketch with at most a few keywords"

    def _create_mood_prompt(self) -> str:
        """Generate prompt for LLM to choose artistic mood"""
        return """You are a creative, expressive, opinionated artist about to create a doodle that no one has seen before.

    Choose one evocative word that captures the essence of your artistic vision for this doodle.

    Examples: threshold, echo, becoming, cascade, whisper, fracture, bloom, drift

    Respond with JSON:
    {
        "mood": "your_chosen_word"
    }"""

    def _create_palette_prompt(self) -> str:
        """Generate prompt for LLM to choose color palette"""
        return f"""You are an autonomous artist creating a {self.current_mood} sketch.

Choose a color palette that expresses the {self.current_mood} doodle.
Consider color harmony, emotional impact, and visual balance.

Respond with JSON:
{{
    "palette": ["#color1", "#color2", "#color3", "#color4", "#color5"],
    "palette_name": "descriptive name",
    "reasoning": "why these colors work for this drawing",
    "dominant_color": "#main_color",
    "accent_colors": ["#accent1", "#accent2"]
}}"""

    def _create_shape_prompt(self, canvas_image_data: Optional[str] = None) -> str:
        """Generate prompt for next shape based on current canvas state"""
        canvas_context = ""
        if canvas_image_data:
            canvas_context = "Look at the current canvas state and decide what shape would naturally come next. CRITICAL: Drastically vary the size of each shape. Do not overlap with existing shapes. Find empty areas of the canvas to place your shape. Analyze the existing shapes carefully and choose coordinates that avoid collision."
            # canvas_context = "Look at the current canvas state and decide what shape would naturally come next. You want to cover more blank canvas and tends to not repeat things"
        else:
            canvas_context = "This is the first shape on a blank canvas."

        return f"""You are an autonomous artist creating a {self.current_mood} sketch.

Current state:
- Canvas: {self.canvas_width}x{self.canvas_height}
- Available colors: {', '.join(self.color_palette)}
- Shapes drawn so far: {self.shape_count}/{self.max_shapes}
- Composition state: {self.composition_state}

{canvas_context}

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
- Is it creating an artwork noone has ever seen before?
- Its positioning on the canvas and is it covering too much of the shapes from before?
- Composition that reduces overlap and covers more canvas

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

    def _call_llm(self, prompt: str, image_data: Optional[str] = None) -> Dict:
        """Call LLM with optional image context"""
        try:
            content = prompt
            if image_data:
                content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}}
                ]

            response = openai.ChatCompletion.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a creative artist. Respond only with valid JSON."},
                    {"role": "user", "content": content}
                ],
                temperature=0.9,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()

            # Clean JSON formatting
            if response_text.startswith('```json'):
                response_text = response_text[7:-3]
            elif response_text.startswith('```'):
                response_text = response_text[3:-3]

            return json.loads(response_text)

        except Exception as e:
            print(f"LLM error: {e}")
            return self._create_fallback_shape()

    def _create_fallback_shape(self) -> Dict:
        """Create fallback shape when LLM fails"""
        print("creating fallback shapes")
        shapes = ["rectangle", "circle", "ellipse", "line"]
        shape = random.choice(shapes)
        color = random.choice(self.color_palette) if self.color_palette else "#333333"

        shape_configs = {
            "rectangle": {
                "params": {
                    "x": random.randint(50, self.canvas_width - 150),
                    "y": random.randint(50, self.canvas_height - 150),
                    "width": random.randint(30, 120),
                    "height": random.randint(30, 120)
                }
            },
            "circle": {
                "params": {
                    "x": random.randint(80, self.canvas_width - 80),
                    "y": random.randint(80, self.canvas_height - 80),
                    "diameter": random.randint(40, 100)
                }
            },
            "ellipse": {
                "params": {
                    "x": random.randint(70, self.canvas_width - 70),
                    "y": random.randint(70, self.canvas_height - 70),
                    "width": random.randint(40, 120),
                    "height": random.randint(30, 80)
                }
            },
            "line": {
                "params": {
                    "x1": random.randint(50, self.canvas_width - 50),
                    "y1": random.randint(50, self.canvas_height - 50),
                    "x2": random.randint(50, self.canvas_width - 50),
                    "y2": random.randint(50, self.canvas_height - 50)
                }
            }
        }

        return {
            "shape": shape,
            "params": shape_configs[shape]["params"],
            "options": {
                "stroke": color,
                "strokeWidth": random.randint(1, 4),
                "roughness": random.uniform(0.8, 2.0),
                "bowing": random.uniform(0.2, 1.0)
            },
            "artistic_reasoning": f"Fallback {shape} shape"
        }

    def _validate_shape(self, shape_data: Dict) -> bool:
        """Validate shape data"""
        if not isinstance(shape_data, dict) or "shape" not in shape_data or "params" not in shape_data:
            return False

        shape_type = shape_data["shape"]
        params = shape_data["params"]

        # Basic boundary validation
        try:
            if shape_type == "rectangle":
                x, y, w, h = params["x"], params["y"], params["width"], params["height"]
                return 0 <= x <= self.canvas_width and 0 <= y <= self.canvas_height and w > 0 and h > 0
            elif shape_type == "circle":
                x, y, d = params["x"], params["y"], params["diameter"]
                r = d / 2
                return r <= x <= self.canvas_width - r and r <= y <= self.canvas_height - r and d > 0
            elif shape_type == "line":
                x1, y1, x2, y2 = params["x1"], params["y1"], params["x2"], params["y2"]
                return (0 <= x1 <= self.canvas_width and 0 <= y1 <= self.canvas_height and
                       0 <= x2 <= self.canvas_width and 0 <= y2 <= self.canvas_height)
            return True
        except (KeyError, TypeError, ValueError):
            return False

    def _update_composition_state(self):
        """Update composition phase based on progress"""
        progress = self.shape_count / self.max_shapes if self.max_shapes > 0 else 0

        if progress < 0.3:
            self.composition_state = "starting"
        elif progress < 0.6:
            self.composition_state = "building"
        elif progress < 0.85:
            self.composition_state = "detailing"
        else:
            self.composition_state = "finishing"

    def initialize_session(self, test_mode=True) -> Dict:
        """Initialize drawing session with mood and palette"""
        # Choose mood
        if test_mode:
            self.current_mood = random.choice(["geometric", "organic", "expressive", "minimal"])
        else:
            # mood_response = self._call_llm(self._create_mood_prompt())
            # self.current_mood = mood_response if isinstance(mood_response, str) else "expressive"
            mood_response = self._call_llm(self._create_mood_prompt())
            # print(mood_response)
            mood = list(mood_response.values())[0]
            print(mood)
            self.current_mood = mood

        # Choose palette
        palette_data = self._choose_palette(test_mode)

        session_data = {
            "session_id": self.session_id,
            "mood": self.current_mood,
            "palette": palette_data,
            "canvas_size": {"width": self.canvas_width, "height": self.canvas_height},
            "max_shapes": self.max_shapes,
            "initialized_at": datetime.datetime.now().isoformat()
        }

        # Save session initialization
        self._save_session_state(session_data, "initialized")

        return session_data

    def _choose_palette(self, test_mode=False) -> Dict:
        """Choose color palette"""
        if test_mode:
            palette_data = self._generate_fallback_palette()
        else:
            palette_data = self._call_llm(self._create_palette_prompt())
            if not self._validate_palette(palette_data):
                palette_data = self._generate_fallback_palette()

        self.color_palette = palette_data.get("palette", ["#333333"])
        self.palette_reasoning = palette_data.get("reasoning", "")
        print(self.color_palette,self.palette_reasoning)
        return palette_data

    def _validate_palette(self, palette_data: Dict) -> bool:
        """Validate palette data"""
        if not isinstance(palette_data, dict):
            return False

        palette = palette_data.get("palette", [])
        if not isinstance(palette, list) or len(palette) < 3:
            return False

        # Validate hex colors
        for color in palette:
            if not isinstance(color, str) or not color.startswith('#') or len(color) != 7:
                return False

        return True

    def _generate_fallback_palette(self) -> Dict:
        """Generate fallback palette"""
        print("Generate Fallback Palette.")
        palettes = [
            {
                "palette": ["#2c3e50", "#e74c3c", "#f39c12", "#f1c40f", "#27ae60"],
                "palette_name": "Bold & Energetic",
                "reasoning": "Strong contrasts for dynamic expression"
            },
            {
                "palette": ["#34495e", "#95a5a6", "#ecf0f1", "#3498db", "#2980b9"],
                "palette_name": "Cool Serenity",
                "reasoning": "Calming blues and grays"
            },
            {
                "palette": ["#8e44ad", "#9b59b6", "#e91e63", "#f06292", "#ad1457"],
                "palette_name": "Purple Dreams",
                "reasoning": "Rich purples and pinks"
            }
        ]
        return random.choice(palettes)

    def generate_next_shape(self, canvas_image_data: Optional[str] = None, test_mode=False) -> Dict:
        """Generate the next shape based on current canvas state"""
        self._update_composition_state()

        if test_mode:
            shape_data = self._create_fallback_shape()
        else:
            prompt = self._create_shape_prompt(canvas_image_data)
            shape_data = self._call_llm(prompt, canvas_image_data)

        if not self._validate_shape(shape_data):
            shape_data = self._create_fallback_shape()

        self.shapes.append(shape_data)
        self.shape_count += 1

        # Save canvas state
        if canvas_image_data:
            self._save_canvas_state(canvas_image_data, self.shape_count - 1)

        return {
            "shape": shape_data,
            "shape_number": self.shape_count,
            "total_shapes": self.max_shapes,
            "composition_state": self.composition_state,
            "is_complete": self.shape_count >= self.max_shapes
        }

    def _save_canvas_state(self, canvas_image_data: str, shape_number: int):
        """Save current canvas state to file"""
        try:
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            filename = f"{CANVAS_DIR}/session_{self.session_id}_shape_{shape_number:02d}_{timestamp}.png"

            # Decode base64 image data
            image_data = base64.b64decode(canvas_image_data)

            with open(filename, 'wb') as f:
                f.write(image_data)

            print(f"💾 Saved canvas state: {filename}")

        except Exception as e:
            print(f"❌ Error saving canvas state: {e}")

    def _save_session_state(self, session_data: Dict, state_type: str):
        """Save session state to file"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{OUTPUT_DIR}/session_{self.session_id}_{state_type}_{timestamp}.json"

            with open(filename, 'w') as f:
                json.dump(session_data, f, indent=2)

            print(f"💾 Saved session state: {filename}")

        except Exception as e:
            print(f"❌ Error saving session state: {e}")

    def get_session_summary(self) -> Dict:
        """Get current session summary"""
        return {
            "session_id": self.session_id,
            "mood": self.current_mood,
            "palette": self.color_palette,
            "shapes_created": self.shape_count,
            "max_shapes": self.max_shapes,
            "composition_state": self.composition_state,
            "progress": self.shape_count / self.max_shapes if self.max_shapes > 0 else 0
        }

# Global agent instance
drawing_agent = None

@app.route('/api/initialize', methods=['POST'])
def initialize_session():
    """Initialize a new drawing session"""
    global drawing_agent

    try:
        data = request.get_json() or {}
        canvas_width = data.get('canvas_width', 800)
        canvas_height = data.get('canvas_height', 600)
        test_mode = data.get('test_mode', False)

        # Create new agent
        drawing_agent = RoughDrawingAgent(canvas_width, canvas_height)
        session_data = drawing_agent.initialize_session(test_mode)

        return jsonify({
            "success": True,
            "session": session_data,
            "message": f"Initialized {session_data['mood']} drawing session"
        })

    except Exception as e:
        print(f"Error in initialize_session: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to initialize session"
        }), 500

@app.route('/api/next-shape', methods=['POST'])
def generate_next_shape():
    """Generate the next shape based on current canvas"""
    global drawing_agent

    try:
        if not drawing_agent:
            return jsonify({
                "success": False,
                "error": "No active session",
                "message": "Please initialize a session first"
            }), 400

        data = request.get_json() or {}
        canvas_image_data = data.get('canvas_image')  # Base64 encoded PNG
        test_mode = data.get('test_mode', False)

        result = drawing_agent.generate_next_shape(canvas_image_data, test_mode)

        return jsonify({
            "success": True,
            "result": result,
            "session_summary": drawing_agent.get_session_summary(),
            "message": f"Generated shape {result['shape_number']}/{result['total_shapes']}"
        })

    except Exception as e:
        print(f"Error in generate_next_shape: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate next shape"
        }), 500

@app.route('/api/session-status', methods=['GET'])
def get_session_status():
    """Get current session status"""
    global drawing_agent

    if not drawing_agent:
        return jsonify({
            "success": False,
            "message": "No active session"
        })

    return jsonify({
        "success": True,
        "session": drawing_agent.get_session_summary()
    })

@app.route('/api/test', methods=['GET'])
def test_api():
    """Test API endpoint"""
    return jsonify({
        "success": True,
        "message": "API is working",
        "openai_configured": bool(openai.api_key and openai.api_key != "your-api-key-here"),
        "output_dirs_exist": {
            "illustrations": os.path.exists(OUTPUT_DIR),
            "canvas_states": os.path.exists(CANVAS_DIR)
        }
    })

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def demo_page():
    """Enhanced demo page with step-by-step generation"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Doodle Agent</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🎨</text></svg>">
    <script src="https://unpkg.com/roughjs@4.5.2/bundled/rough.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #2980b9; }
        button:disabled { background: #bdc3c7; cursor: not-allowed; }
        .canvas-container { display: flex; gap: 20px; }
        .canvas-section { flex: 1; }
        canvas { border: 2px solid #ddd; background: white; border-radius: 4px; width: 100%; max-width: 400px; }
        .info-panel { flex: 1; background: #ecf0f1; padding: 15px; border-radius: 4px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #d5edda; color: #155724; }
        .error { background: #f8d7da; color: #721c24; }
        .progress { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .shape-info { background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 4px solid #3498db; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎨 Doodle Agent</h1>
        <p>Watch an AI create expressive sketches one shape at a time, analyzing the canvas as it evolves.</p>

        <div class="controls">
            <button onclick="initializeSession()">Start New Session</button>
            <button id="nextShapeBtn" onclick="generateNextShape()" disabled>Next Shape</button>
            <button onclick="autoGenerate()" id="autoBtn" disabled>Auto Generate</button>
            <label>Speed:
                <select id="speedControl">
                    <option value="3000">Slow (3s)</option>
                    <option value="2000" selected>Normal (2s)</option>
                    <option value="1000">Fast (1s)</option>
                    <option value="500">Very Fast (0.5s)</option>
                </select>
            </label>
            <button onclick="clearCanvas()">Clear Canvas</button>
            <button onclick="testAPI()">Test API</button>
        </div>

        <div id="status"></div>

        <div class="canvas-container">
            <div class="canvas-section">
                <h3>Drawing Canvas</h3>
                <canvas id="drawingCanvas" width="400" height="300"></canvas>
            </div>

            <div class="info-panel">
                <h3>Session Info</h3>
                <div id="sessionInfo">No active session</div>

                <div id="progressInfo" style="display: none;">
                    <h4>Progress</h4>
                    <div id="progressBar" style="background: #ddd; height: 20px; border-radius: 10px;">
                        <div id="progressFill" style="background: #3498db; height: 100%; border-radius: 10px; width: 0%; transition: width 0.3s;"></div>
                    </div>
                    <div id="progressText"></div>
                </div>

                <div id="shapeHistory">
                    <h4>Shape History</h4>
                    <div id="shapeList"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let canvas = document.getElementById('drawingCanvas');
        let rc, ctx;
        let currentSession = null;
        let isAutoGenerating = false;

        window.addEventListener('load', function() {
            if (typeof rough !== 'undefined') {
                rc = rough.canvas(canvas);
                ctx = canvas.getContext('2d');
                showStatus('Ready! Click "Start New Session" to begin.', false);
            } else {
                showStatus('Error: Rough.js failed to load', true);
            }
        });

        function showStatus(message, isError = false) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = 'status ' + (isError ? 'error' : 'success');
        }

        function updateSessionInfo(session) {
            const info = document.getElementById('sessionInfo');
            info.innerHTML = `
                <strong>Mood:</strong> ${session.mood}<br>
                <strong>Palette:</strong> ${session.palette ? session.palette : 'Loading...'}<br>
                <strong>Canvas:</strong> ${session.canvas_size ? session.canvas_size.width + 'x' + session.canvas_size.height : 'Unknown'}
            `;
        }

        function updateProgress(summary) {
            const progressInfo = document.getElementById('progressInfo');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');

            const progress = (summary.progress * 100).toFixed(1);
            progressFill.style.width = progress + '%';
            progressText.textContent = `${summary.shapes_created}/${summary.max_shapes} shapes (${progress}%)`;
            progressInfo.style.display = 'block';
        }

        function addShapeToHistory(shape, shapeNumber) {
            const shapeList = document.getElementById('shapeList');
            const shapeDiv = document.createElement('div');
            shapeDiv.className = 'shape-info';
            shapeDiv.style.opacity = '0';
            shapeDiv.style.transform = 'translateX(-20px)';
            shapeDiv.style.transition = 'all 0.3s ease';
            shapeDiv.innerHTML = `
                <strong>Shape ${shapeNumber}:</strong> ${shape.shape}<br>
                <em>${shape.artistic_reasoning || 'Generated shape'}</em>
            `;
            shapeList.appendChild(shapeDiv);

            // Animate in the new shape
            setTimeout(() => {
                shapeDiv.style.opacity = '1';
                shapeDiv.style.transform = 'translateX(0)';
            }, 100);

            // Scroll to show the latest shape
            shapeDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function clearCanvas() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            document.getElementById('shapeList').innerHTML = '';
            document.getElementById('progressInfo').style.display = 'none';
            currentSession = null;
            document.getElementById('nextShapeBtn').disabled = true;
            document.getElementById('autoBtn').disabled = true;
        }

        function getCanvasImageData() {
            return canvas.toDataURL('image/png').split(',')[1]; // Remove data:image/png;base64, prefix
        }

        function drawShape(shape) {
            if (!rc) return;

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

        async function initializeSession() {
            showStatus('Initializing new session...', false);
            clearCanvas();

            try {
                const response = await fetch('/api/initialize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        canvas_width: canvas.width,
                        canvas_height: canvas.height,
                        test_mode: false
                    })
                });

                const data = await response.json();

                if (data.success) {
                    currentSession = data.session;
                    updateSessionInfo(currentSession);
                    showStatus(data.message, false);
                    document.getElementById('nextShapeBtn').disabled = false;
                    document.getElementById('autoBtn').disabled = false;
                } else {
                    showStatus('Error: ' + data.message, true);
                }
            } catch (error) {
                showStatus('Network error: ' + error.message, true);
            }
        }

        async function generateNextShape() {
            if (!currentSession) {
                showStatus('Please initialize a session first', true);
                return;
            }

            showStatus('Generating next shape...', false);

            try {
                const canvasImage = getCanvasImageData();

                const response = await fetch('/api/next-shape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        canvas_image: canvasImage,
                        test_mode: false
                    })
                });

                const data = await response.json();

                if (data.success) {
                    const { result, session_summary } = data;

                    drawShape(result.shape);
                    addShapeToHistory(result.shape, result.shape_number);
                    updateProgress(session_summary);

                    showStatus(`Shape ${result.shape_number}/${result.total_shapes} - ${result.composition_state}`, false);

                    if (result.is_complete) {
                        showStatus('Drawing complete! 🎉', false);
                        document.getElementById('nextShapeBtn').disabled = true;
                        document.getElementById('autoBtn').disabled = true;
                        isAutoGenerating = false;
                    }
                } else {
                    showStatus('Error: ' + data.message, true);
                    isAutoGenerating = false;
                }
            } catch (error) {
                showStatus('Network error: ' + error.message, true);
                isAutoGenerating = false;
            }
        }

        async function autoGenerate() {
            if (isAutoGenerating) {
                isAutoGenerating = false;
                document.getElementById('autoBtn').textContent = 'Auto Generate';
                showStatus('Auto-generation stopped', false);
                return;
            }

            isAutoGenerating = true;
            document.getElementById('autoBtn').textContent = 'Stop Auto';

            // Get speed from control
            const speed = parseInt(document.getElementById('speedControl').value);

            while (isAutoGenerating && currentSession) {
                // Show what we're doing
                const currentShapeNum = document.querySelectorAll('.shape-info').length + 1;
                showStatus(`🎨 Auto-generating shape ${currentShapeNum}...`, false);

                // Highlight the canvas during generation
                canvas.style.boxShadow = '0 0 20px #3498db';

                await generateNextShape();

                // Remove highlight
                canvas.style.boxShadow = 'none';

                if (isAutoGenerating) {
                    // Show completion of this step
                    const newShapeNum = document.querySelectorAll('.shape-info').length;
                    showStatus(`✅ Shape ${newShapeNum} completed. Next shape in ${speed/1000}s...`, false);

                    // Wait based on speed setting
                    await new Promise(resolve => setTimeout(resolve, speed));
                }

                // Check if drawing is complete
                const response = await fetch('/api/session-status');
                const statusData = await response.json();
                if (statusData.success && statusData.session.shapes_created >= statusData.session.max_shapes) {
                    isAutoGenerating = false;
                    break;
                }
            }

            document.getElementById('autoBtn').textContent = 'Auto Generate';
            canvas.style.boxShadow = 'none';

            if (!isAutoGenerating) {
                showStatus('🎉 Auto-generation completed!', false);
            }
        }

        async function testAPI() {
            try {
                const response = await fetch('/api/test');
                const data = await response.json();
                showStatus(`API Test: ${data.message} | OpenAI: ${data.openai_configured}`, false);
            } catch (error) {
                showStatus('API test failed: ' + error.message, true);
            }
        }
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
