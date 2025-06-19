#!/usr/bin/env python3
"""
LLM Artist Backend - A Claude-powered creative agent for the flowing particle canvas
This backend receives canvas snapshots, analyzes them with Claude, and returns artistic actions.
"""

import asyncio
import websockets
import json
import base64
import io
import time
from PIL import Image
import anthropic
import os
from datetime import datetime
import random
from dotenv import load_dotenv
load_dotenv()
class LLMArtist:
    def __init__(self):
        # Initialize Claude client
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Artist state
        self.canvas_history = []
        self.last_action_time = time.time()
        self.artistic_memory = []
        self.current_theme = None
        self.stroke_count = 0
        self.session_start = datetime.now()
        
        # Available colors for the artist
        self.color_palette = [
            "#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", 
            "#feca57", "#ff9ff3", "#54a0ff", "#5f27cd",
            "#26de81", "#fc5c65", "#fd79a8", "#fdcb6e",
            "#6c5ce7", "#fd79a8", "#a29bfe", "#fab1a0"
        ]
        
        print("🎨 LLM Artist initialized!")
        print("📡 Starting WebSocket server on localhost:8765")

    def encode_image_for_claude(self, image_data):
        """Convert base64 image data to format suitable for Claude's vision API"""
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            # Decode and re-encode to ensure proper format
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize if too large (Claude has limits)
            if image.width > 512 or image.height > 512:
                image.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            # Convert back to base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
        except Exception as e:
            print(f"❌ Error encoding image: {e}")
            return None

    async def analyze_canvas_with_claude(self, canvas_data, current_settings, ai_position):
        """Send canvas image to Claude for creative analysis and next action decision"""
        try:
            # Encode image properly
            image_b64 = self.encode_image_for_claude(canvas_data['image'])
            if not image_b64:
                return None
            
            # Prepare context about the session
            session_info = f"""
Session started: {self.session_start.strftime('%H:%M')}
Strokes made: {self.stroke_count}
Current theme: {self.current_theme or 'Exploring'}
Canvas size: {canvas_data['canvas_width']}x{canvas_data['canvas_height']}
Current position: ({ai_position['x']:.0f}, {ai_position['y']:.0f})
"""

            # Prepare recent artistic memory
            memory_context = ""
            if self.artistic_memory:
                recent_memories = self.artistic_memory[-3:]  # Last 3 actions
                memory_context = "Recent actions:\n" + "\n".join(recent_memories)

            prompt = f"""You are a curious AI artist with a flowing particle brush system. You can see your canvas and experiment with different parameter combinations to discover their visual effects, then use those discoveries to create art.

YOUR MISSION: 
🔬 EXPERIMENT with different parameter combinations to understand their effects
🎨 TEST extreme values to discover new textures and patterns  
🚀 BUILD compositions using your experimental discoveries
🎯 ADJUST parameters dynamically as you create

CURRENT STATE:
{session_info}

CURRENT PARAMETERS:
- Brush size: {current_settings['brush_size']} (5-50)
- Flow rate: {current_settings['flow_rate']} (0.1-2.0) 
- Particle count: {current_settings['particle_count']} (5-30)
- Turbulence: {current_settings['turbulence']} (0-10)
- Color: {current_settings['color']}

{memory_context}

AVAILABLE ACTIONS:
1. **move_to**: Jump to coordinates and paint there
2. **draw_line**: Draw from current position to target coordinates  
3. **draw_curve**: Draw bezier curve using control point

PARAMETER EXPERIMENTATION STRATEGY:
- Try EXTREME combinations: What does max turbulence + min brush size create?
- Test CONTRASTS: Follow high chaos with precise control
- DOCUMENT discoveries: Explain what each combination produces
- BUILD on findings: Use successful experiments in compositions

EXAMPLE EXPERIMENTAL ACTIONS:

Testing chaos texture:
{{
    "action": "move_to",
    "x": 200, "y": 200,
    "brush_size": 45, "turbulence": 9, "particle_count": 25, "flow_rate": 1.8,
    "color": "#ff6b6b",
    "thought": "Testing maximum chaos parameters - what texture emerges?"
}}

Precision contrast:
{{
    "action": "draw_line", 
    "to_x": 400, "to_y": 200,
    "brush_size": 8, "turbulence": 0, "particle_count": 10, "flow_rate": 0.3,
    "thought": "Adding precise controlled line to contrast with chaos"
}}

Organic discovery:
{{
    "action": "draw_curve",
    "control_x": 250, "control_y": 100, "end_x": 400, "end_y": 300,
    "brush_size": 25, "turbulence": 5, "particle_count": 20,
    "color": "#4ecdc4", 
    "thought": "Medium turbulence + larger brush for organic flowing effect"
}}

EXPERIMENTAL MINDSET:
- What happens if I use opposite extremes in adjacent areas?
- How do different colors interact with different turbulence levels?
- What textures emerge from unusual flow rate + particle count combinations?
- Can I create energy gradients by varying parameters across strokes?

ANALYZE THE CURRENT CANVAS:
Look at what exists and decide:
- What parameter combinations might have created existing effects?
- What's missing compositionally?
- How can you experiment with unexplored parameter ranges?
- What would create interesting contrast or harmony?

Respond with a JSON action that either EXPERIMENTS with new parameter combinations or BUILDS upon previous discoveries."""
            # Send to Claude
            content = [{"type": "text","text": prompt}]
            if image_b64 is not None:
                content.append({
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            })
            message = self.client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": content,
                    }
                ]
            )
            
            # Parse Claude's response
            response_text = message.content[0].text.strip()
            print(f"🤖 Claude's response: {response_text}")
            # Extract JSON from response (Claude might add explanation before/after)
            try:
                # Try to find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx:end_idx]
                    action = json.loads(json_str)
                    
                    # Validate and sanitize the action
                    action = self.validate_action(action, canvas_data)
                    
                    # Store in artistic memory
                    if action.get('thought'):
                        self.artistic_memory.append(f"Action {self.stroke_count}: {action['thought']}")
                        if len(self.artistic_memory) > 10:
                            self.artistic_memory.pop(0)
                    
                    self.stroke_count += 1
                    self.last_action_time = time.time()
                    
                    return action
                else:
                    print("❌ No valid JSON found in Claude's response")
                    return self.get_fallback_action(canvas_data)
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"Raw response: {response_text}")
                return self.get_fallback_action(canvas_data)
                
        except Exception as e:
            print(f"❌ Error calling Claude API: {e}")
            return self.get_fallback_action(canvas_data)

    def validate_action(self, action, canvas_data):
        """Validate and sanitize the action from Claude"""
        canvas_width = canvas_data['canvas_width']
        canvas_height = canvas_data['canvas_height']
        
        # Ensure coordinates are within bounds
        coord_fields = ['x', 'y', 'to_x', 'to_y', 'control_x', 'control_y', 'end_x', 'end_y']
        for field in coord_fields:
            if field in action:
                if 'x' in field:
                    action[field] = max(0, min(canvas_width, action[field]))
                elif 'y' in field:
                    action[field] = max(0, min(canvas_height, action[field]))
        
        # Validate brush parameters
        if 'brush_size' in action:
            action['brush_size'] = max(5, min(50, action['brush_size']))
        if 'flow_rate' in action:
            action['flow_rate'] = max(0.1, min(2.0, action['flow_rate']))
        if 'particle_count' in action:
            action['particle_count'] = max(5, min(30, action['particle_count']))
        if 'turbulence' in action:
            action['turbulence'] = max(0, min(10, action['turbulence']))
        
        # Validate color format
        if 'color' in action:
            color = action['color']
            if not (isinstance(color, str) and color.startswith('#') and len(color) == 7):
                action['color'] = random.choice(self.color_palette)
        
        # Ensure valid action type (only 3 core actions)
        valid_actions = ['move_to', 'draw_line', 'draw_curve']
        if action.get('action') not in valid_actions:
            action['action'] = 'move_to'
            action['x'] = canvas_width // 2
            action['y'] = canvas_height // 2
            action['thought'] = 'Defaulting to safe move action'
        
        return action

    def get_fallback_action(self, canvas_data):
        """Generate a simple experimental fallback action if Claude fails"""
        canvas_width = canvas_data['canvas_width']
        canvas_height = canvas_data['canvas_height']
        
        # Simple experimental actions using only the 3 core types
        experimental_actions = [
            {
                "action": "move_to",
                "x": random.randint(50, canvas_width - 50),
                "y": random.randint(50, canvas_height - 50),
                "brush_size": random.randint(10, 40),
                "turbulence": random.randint(2, 8),
                "particle_count": random.randint(8, 25),
                "flow_rate": 0.5 + random.random() * 1.5,
                "color": random.choice(self.color_palette),
                "thought": "Experimenting with random parameter combination"
            },
            {
                "action": "draw_line",
                "to_x": random.randint(100, canvas_width - 100),
                "to_y": random.randint(100, canvas_height - 100),
                "brush_size": random.randint(8, 35),
                "turbulence": random.randint(0, 6),
                "flow_rate": 0.8 + random.random() * 1.0,
                "color": random.choice(self.color_palette),
                "thought": "Drawing experimental line with varied parameters"
            },
            {
                "action": "draw_curve",
                "control_x": random.randint(150, canvas_width - 150),
                "control_y": random.randint(100, canvas_height - 200),
                "end_x": random.randint(150, canvas_width - 150),
                "end_y": random.randint(150, canvas_height - 150),
                "brush_size": random.randint(12, 30),
                "turbulence": random.randint(1, 7),
                "particle_count": random.randint(10, 25),
                "thought": "Exploring curved motions with experimental settings"
            }
        ]
        
        return random.choice(experimental_actions)

    async def handle_client(self, websocket, path):
        """Handle WebSocket connection from the frontend"""
        print(f"🌐 Client connected from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if data['type'] == 'canvas_state':
                        print("📸 Received canvas state, analyzing with Claude...")
                        
                        # Send thinking indicator
                        await websocket.send(json.dumps({
                            "type": "thinking",
                            "show": True,
                            "message": "🤖 Analyzing canvas and planning next move..."
                        }))
                        
                        # Analyze with Claude
                        action = await self.analyze_canvas_with_claude(
                            data, 
                            data['current_settings'], 
                            data['ai_position']
                        )
                        
                        # Stop thinking indicator
                        await websocket.send(json.dumps({
                            "type": "thinking", 
                            "show": False
                        }))
                        
                        if action:
                            # Send action to frontend
                            action['type'] = 'action'
                            await websocket.send(json.dumps(action))
                            print(f"✨ Sent action: {action.get('action', 'unknown')} - {action.get('thought', '')}")
                        else:
                            await websocket.send(json.dumps({
                                "type": "action",
                                "action": "move_to",
                                "x": 100,
                                "y": 100,
                                "thought": "Having trouble thinking, making a simple mark"
                            }))
                    
                except json.JSONDecodeError:
                    print("❌ Invalid JSON received from client")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            print("🔌 Client disconnected")
        except Exception as e:
            print(f"❌ WebSocket error: {e}")

    async def start_server(self):
        """Start the WebSocket server"""
        try:
            server = await websockets.serve(
                self.handle_client, 
                "localhost", 
                8765,
                ping_interval=30,
                ping_timeout=10
            )
            print("🎨 LLM Artist Backend is running!")
            print("🌐 WebSocket server started on ws://localhost:8765")
            print("💡 Make sure to set your ANTHROPIC_API_KEY environment variable")
            print("🎯 Open the HTML canvas in your browser to start creating!")
            
            await server.wait_closed()
            
        except Exception as e:
            print(f"❌ Failed to start server: {e}")

def main():
    """Main entry point"""
    # Check for API key
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set!")
        print("💡 Set it with: export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    print("🎨 Starting LLM Artist Backend...")
    print("🤖 Powered by Claude for autonomous creativity")
    
    artist = LLMArtist()
    
    try:
        asyncio.run(artist.start_server())
    except KeyboardInterrupt:
        print("\n👋 LLM Artist Backend stopped by user")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()