import json
import base64
import anthropic
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class DrawingAction:
    """Represents a single drawing action to be executed"""
    brush: str
    color: str
    strokes: List[Dict]
    reasoning: str

class DrawingAgent:
    """
    LLM-powered drawing agent that analyzes text prompts and canvas images
    to generate specific drawing actions for the painting interface.
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Initialize conversation memory
        self.messages = []
        self.system_sent = False
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_and_plan(self, text_prompt: str, canvas_image_path: str) -> DrawingAction:
        """
        Analyze the text prompt and current canvas to generate a drawing action.
        
        Args:
            text_prompt: User's description of what to draw
            canvas_image_path: Path to current canvas image
            
        Returns:
            DrawingAction object with specific drawing instructions
        """
        
        # Encode the canvas image
        image_data = self.encode_image(canvas_image_path)
        
        # Prepare the user message
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Text Prompt: {text_prompt}\n\nPlease analyze this prompt and the current canvas image, then provide a drawing action in JSON format."
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
        
        # Add to conversation history
        self.messages.append(user_message)
        
        system_prompt = [{"type": "text", "text": self._get_system_prompt()}]
        try:
            # print(self.messages)
            # Create the response using Anthropic client
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=self.messages,
                system=system_prompt
            )
            
            # Extract the response content
            content = response.content[0].text
            
            # Add assistant response to conversation history
            assistant_message = {
                "role": "assistant",
                "content": [{"type": "text", "text": content}]
            }
            self.messages.append(assistant_message)
            
            # Parse the JSON response - try multiple approaches
            action_data = None
            
            # Method 1: Look for JSON block in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                try:
                    action_data = json.loads(json_str)
                except json.JSONDecodeError as json_error:
                    print(f"JSON parsing error: {json_error}")
                    print(f"Attempted to parse: {json_str}")
                    
                    # Method 2: Try to fix common JSON issues
                    try:
                        # Remove any trailing commas or extra characters
                        json_str = json_str.rstrip(', \n\r\t')
                        if not json_str.endswith('}'):
                            json_str += '}'
                        action_data = json.loads(json_str)
                    except:
                        print("Failed to fix JSON, trying alternative parsing...")
            
            # Method 3: Try to extract JSON from markdown code blocks
            if action_data is None:
                import re
                json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
                matches = re.findall(json_pattern, content, re.DOTALL)
                if matches:
                    try:
                        action_data = json.loads(matches[0])
                    except:
                        print("Failed to parse JSON from code blocks")
            
            # Method 4: Extract essential information from complex responses
            if action_data is None or not self._validate_action_data(action_data):
                print(action_data)
                action_data = self._extract_from_complex_response(content)
            
            # If we still don't have valid data, create a default action
            if action_data is None:
                print(f"Could not parse JSON from response: {content}")
                action_data = {
                    "brush": "flowing",
                    "color": "#ff6b6b",
                    "strokes": [],
                    "reasoning": "Default action due to parsing failure"
                }
            
            # Validate required fields
            required_fields = ["brush", "color", "strokes"]
            missing_fields = [field for field in required_fields if field not in action_data]
            
            if missing_fields:
                print(f"Warning: Missing required fields in API response: {missing_fields}")
                print(f"Full response: {content}")
                # Fill in missing fields with defaults
                action_data = {
                    "brush": action_data.get("brush", "flowing"),
                    "color": action_data.get("color", "#ff6b6b"),
                    "strokes": action_data.get("strokes", []),
                    "reasoning": action_data.get("reasoning", "Default action due to missing fields")
                }
            
            return DrawingAction(
                brush=self._validate_brush_type(action_data["brush"]),
                color=action_data["color"],
                strokes=self._enhance_strokes(action_data["strokes"]),
                reasoning=action_data.get("reasoning", "")
            )
                
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            print(f"Full error details: {str(e)}")
            # Return a default action
            return DrawingAction(
                brush="flowing",
                color="#ff6b6b",
                strokes=[],
                reasoning="Default action due to API error"
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the drawing agent"""
        with open("agent_prompt.md", "r") as f:
            return f.read()
        
    
    def _get_drawing_tool_schema(self):
        return {
            "name": "create_drawing_action",
            "description": "Create a drawing action with brush, color, strokes, and reasoning",
            "input_schema": {
                "type": "object",
                "properties": {
                    "brush": {
                        "type": "string",
                        "enum": ["flowing", "watercolor", "crayon", "oil"],
                        "description": "The brush type to use for drawing"
                    },
                    "color": {
                        "type": "string",
                        "pattern": "^#[0-9A-Fa-f]{6}$",
                        "description": "Hex color code for the brush"
                    },
                    "strokes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "minItems": 3,
                                    "maxItems": 8,
                                    "description": "X coordinates for stroke points (50-750px)"
                                },
                                "y": {
                                    "type": "array",
                                    "items": {"type": "integer"},
                                    "minItems": 3,
                                    "maxItems": 8,
                                    "description": "Y coordinates for stroke points (50-550px)"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Brief description of what this stroke creates"
                                }
                            },
                            "required": ["x", "y", "description"]
                        },
                        "description": "Array of strokes to execute"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of brush choice and approach"
                    }
                },
                "required": ["brush", "color", "strokes", "reasoning"]
            }
        }
    
    def _parse_json_from_text(self, content: str) -> Optional[dict]:
        """Parse JSON from text response as fallback"""
        # Method 1: Look for JSON block in the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Method 2: Try to extract JSON from markdown code blocks
        import re
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, content, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass
        
        return None
    
    def _validate_action_data(self, action_data: dict) -> bool:
        """Validate that action_data has the required structure"""
        if not isinstance(action_data, dict):
            return False
        
        # Check for required fields
        required_fields = ["brush", "color", "strokes"]
        for field in required_fields:
            if field not in action_data:
                return False
        
        # Validate brush type
        brush = action_data["brush"]
        if isinstance(brush, list):
            return False  # Brush should be a string, not a list
        
        # Validate strokes
        strokes = action_data["strokes"]
        if not isinstance(strokes, list):
            return False
        
        return True
    
    def _extract_from_complex_response(self, content: str) -> dict:
        """Extract essential drawing information from complex API responses"""
        try:
            # Try to find any JSON-like structure
            import re
            
            # Look for brush information
            brush_patterns = [
                r'"brush":\s*"([^"]+)"',
                r'"brush":\s*\[([^\]]+)\]',
                r'brush[:\s]+([a-zA-Z]+)'
            ]
            
            brush = "flowing"  # default
            for pattern in brush_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    brush_value = match.group(1).strip()
                    if brush_value in ["watercolor", "crayon", "oil", "flowing"]:
                        brush = brush_value
                    elif "particle" in brush_value.lower():
                        brush = "flowing"
                    elif "water" in brush_value.lower():
                        brush = "watercolor"
                    elif "crayon" in brush_value.lower():
                        brush = "crayon"
                    elif "oil" in brush_value.lower() or "paint" in brush_value.lower():
                        brush = "oil"
                    break
            
            # Look for color information
            color_patterns = [
                r'"color":\s*"([^"]+)"',
                r'#[0-9A-Fa-f]{6}',
                r'colors?[:\s]*\{[^}]+\}'
            ]
            
            color = "#ff6b6b"  # default
            for pattern in color_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    if pattern == r'#[0-9A-Fa-f]{6}':
                        color = matches[0]  # Use first hex color found
                    elif '"color":' in pattern:
                        color = matches[0]
                    break
            
            # Look for stroke information
            stroke_patterns = [
                r'"strokes":\s*\[([^\]]+)\]',
                r'"x":\s*\[([^\]]+)\]',
                r'"y":\s*\[([^\]]+)\]'
            ]
            
            strokes = []
            for pattern in stroke_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Try to extract coordinate arrays
                    try:
                        # Look for x and y coordinate arrays
                        x_matches = re.findall(r'"x":\s*\[([^\]]+)\]', content)
                        y_matches = re.findall(r'"y":\s*\[([^\]]+)\]', content)
                        
                        if x_matches and y_matches:
                            # Parse coordinate arrays
                            x_coords = [int(x.strip()) for x in x_matches[0].split(',')]
                            y_coords = [int(y.strip()) for y in y_matches[0].split(',')]
                            
                            if len(x_coords) == len(y_coords) and len(x_coords) > 0:
                                strokes.append({
                                    "x": x_coords,
                                    "y": y_coords,
                                    "description": "Extracted stroke"
                                })
                    except:
                        pass
                    break
            
            # If no strokes found, create a simple default stroke
            if not strokes:
                strokes = [{
                    "x": [100, 110, 120, 130, 140],
                    "y": [100, 105, 110, 115, 120],
                    "description": "Default stroke"
                }]
            
            return {
                "brush": brush,
                "color": color,
                "strokes": strokes,
                "reasoning": "Extracted from complex response"
            }
            
        except Exception as e:
            print(f"Error extracting from complex response: {e}")
            return None
    
    def reset_conversation(self):
        """Reset the conversation memory to start fresh"""
        self.messages = []
        self.system_sent = False
    
    def get_conversation_length(self) -> int:
        """Get the current length of the conversation"""
        return len(self.messages)
    
    def _validate_brush_type(self, brush_type: str) -> str:
        """Validate and correct brush type if needed"""
        valid_brushes = ["flowing", "watercolor", "crayon", "oil"]
        
        # Direct match
        if brush_type in valid_brushes:
            return brush_type
        
        # Handle common variations
        brush_lower = brush_type.lower()
        if "particle" in brush_lower or "flowing" in brush_lower:
            return "flowing"
        elif "water" in brush_lower or "watercolor" in brush_lower:
            return "watercolor"
        elif "crayon" in brush_lower or "wax" in brush_lower:
            return "crayon"
        elif "oil" in brush_lower or "paint" in brush_lower:
            return "oil"
        
        # Default to flowing if no match
        print(f"Warning: Unknown brush type '{brush_type}', using 'flowing' instead")
        return "flowing"
    
    def _enhance_strokes(self, strokes: List[Dict]) -> List[Dict]:
        """Enhance strokes by converting single points to multi-point strokes"""
        enhanced_strokes = []
        
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                # Check if this is already a multi-point stroke
                if isinstance(stroke["x"], list) and isinstance(stroke["y"], list):
                    # Already multi-point, keep as is
                    enhanced_strokes.append(stroke)
                else:
                    # Single point - convert to multi-point stroke
                    x, y = stroke["x"], stroke["y"]
                    
                    # Create a small multi-point stroke around the single point
                    # This creates a more natural stroke effect
                    x_points = [x - 5, x - 2, x, x + 2, x + 5]
                    y_points = [y - 5, y - 2, y, y + 2, y + 5]
                    
                    enhanced_stroke = {
                        "x": x_points,
                        "y": y_points,
                        "description": stroke.get("description", "Enhanced stroke")
                    }
                    enhanced_strokes.append(enhanced_stroke)
            else:
                # Keep other stroke formats as is
                enhanced_strokes.append(stroke)
        
        return enhanced_strokes
    
    def execute_action(self, action: DrawingAction) -> Dict:
        """
        Convert a DrawingAction into executable commands for the painting interface.
        
        Args:
            action: DrawingAction object with drawing instructions
            
        Returns:
            Dictionary with commands to execute on the painting interface
        """
        
        commands = {
            "setBrush": self._validate_brush_type(action.brush),
            "setColor": action.color,
            "strokes": action.strokes,
            "reasoning": action.reasoning
        }
        return commands
    
    def draw_sequentially(self, prompts: List[str], canvas_image_path: str) -> List[DrawingAction]:
        """
        Process multiple drawing prompts sequentially, updating the canvas after each action.
        
        Args:
            prompts: List of text prompts to process
            canvas_image_path: Path to the canvas image (will be updated after each action)
            
        Returns:
            List of DrawingAction objects for each prompt
        """
        
        actions = []
        
        for i, prompt in enumerate(prompts):
            print(f"Processing prompt {i+1}/{len(prompts)}: {prompt}")
            
            # Analyze current state and generate action
            action = self.analyze_and_plan(prompt, canvas_image_path)
            actions.append(action)
            
            # Execute the action (this would interface with the painting system)
            commands = self.execute_action(action)
            # print(f"Generated action: {action.reasoning}")
            
            # In a real implementation, you would:
            # 1. Send commands to the painting interface
            # 2. Wait for the drawing to complete
            # 3. Capture the updated canvas image
            # 4. Update canvas_image_path
            
            # For now, we'll simulate this with a delay
            time.sleep(2)
            
        return actions

# Example usage
import dotenv
import os
dotenv.load_dotenv()
if __name__ == "__main__":
    # Initialize the agent (you'll need to provide your API key)
    agent = DrawingAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Example prompts for a landscape
    prompts = [
        "Draw a sunset sky with warm orange and pink colors",
        "Add mountain silhouettes in the background",
        "Create a flowing river in the foreground",
        "Add some trees along the riverbank"
    ]
    
    # Process the prompts sequentially
    actions = agent.draw_sequentially(prompts, "current_canvas.png")
    
    # Print the generated actions
    for i, action in enumerate(actions):
        print(f"\nAction {i+1}:")
        print(f"Brush: {action.brush}")
        print(f"Color: {action.color}")
        print(f"Reasoning: {action.reasoning}")
        print(f"Strokes: {len(action.strokes)} stroke(s)") 