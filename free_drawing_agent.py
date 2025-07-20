#!/usr/bin/env python3
"""
Free Drawing Agent for drawing_canvas.html
This agent analyzes the current canvas and freely decides what to draw next,
outputting JSON instructions compatible with the drawing_canvas.html interface.
"""
from __future__ import annotations
import json
import base64
import anthropic
from typing import Dict, List, Optional,Tuple
from dataclasses import dataclass
import time
import os
from dotenv import load_dotenv
import random
from datetime import datetime
from PIL import Image
import numpy as np


# Load environment variables from .env file
load_dotenv()

@dataclass
class DrawingInstruction:
    """Represents a drawing instruction to be executed on drawing_canvas.html"""
    brush: str
    color: str
    strokes: List[Dict]
    thinking: str

class FreeDrawingAgent:
    """
    LLM-powered free drawing agent that analyzes canvas images
    and generates creative drawing instructions for drawing_canvas.html
    """

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022", enable_logging: bool = True):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.enable_logging = enable_logging

        # Brush tracking for variety
        self.recent_brushes = []
        self.max_brush_history = 5

        # Stroke history tracking for spatial reasoning
        self.stroke_history = []
        self.max_stroke_history = 10  # Keep last 10 strokes for context

        # Create logging directory if it doesn't exist
        if self.enable_logging:
            os.makedirs("output/log", exist_ok=True)

            # Create session-level log files with timestamp
            session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_log_file = f"output/log/session_responses_{session_timestamp}.txt"
            self.session_summary_file = f"output/log/session_summary_{session_timestamp}.txt"

            # Initialize log files with headers
            with open(self.session_log_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Drawing Agent Session Log ===\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write(f"Model: {self.model}\n")
                f.write(f"{'='*50}\n\n")

            with open(self.session_summary_file, 'w', encoding='utf-8') as f:
                f.write(f"=== Drawing Agent Session Summary ===\n")
                f.write(f"Started: {datetime.now().isoformat()}\n")
                f.write(f"Model: {self.model}\n")
                f.write(f"{'='*50}\n\n")

            print(f"📝 Session logs initialized:")
            print(f"   Full responses: {self.session_log_file}")
            print(f"   Brush & reasoning: {self.session_summary_file}")
        else:
            self.session_log_file = None
            self.session_summary_file = None

        # Initialize color palette
        self.color_palette = {
            'keppel': {
                'DEFAULT': '#6BB9A4',
                '100': '#132822',
                '200': '#254F44',
                '300': '#387766',
                '400': '#4A9E88',
                '500': '#6BB9A4',
                '600': '#88C7B6',
                '700': '#A6D5C8',
                '800': '#C3E3DB',
                '900': '#E1F1ED'
            },
            'sky_blue': {
                'DEFAULT': '#7FC9E1',
                '100': '#0D2E39',
                '200': '#1B5C72',
                '300': '#288AAB',
                '400': '#46B0D4',
                '500': '#7FC9E1',
                '600': '#99D3E7',
                '700': '#B2DEED',
                '800': '#CCE9F3',
                '900': '#E5F4F9'
            },
            'tea_rose_(red)': {
                'DEFAULT': '#FFD1D1',
                '100': '#5D0000',
                '200': '#BA0000',
                '300': '#FF1717',
                '400': '#FF7474',
                '500': '#FFD1D1',
                '600': '#FFDADA',
                '700': '#FFE3E3',
                '800': '#FFEDED',
                '900': '#FFF6F6'
            },
            'light_red': {
                'DEFAULT': '#FF7878',
                '100': '#4B0000',
                '200': '#970000',
                '300': '#E20000',
                '400': '#FF2F2F',
                '500': '#FF7878',
                '600': '#FF9595',
                '700': '#FFAFAF',
                '800': '#FFCACA',
                '900': '#FFE4E4'
            },
            'jasmine': {
                'DEFAULT': '#FFE978',
                '100': '#4B3F00',
                '200': '#977E00',
                '300': '#E2BD00',
                '400': '#FFDC2F',
                '500': '#FFE978',
                '600': '#FFED95',
                '700': '#FFF2AF',
                '800': '#FFF6CA',
                '900': '#FFFBE4'
            },
            'wisteria': {
                'DEFAULT': '#CF94EE',
                '100': '#2F0A43',
                '200': '#5E1586',
                '300': '#8E1FC9',
                '400': '#B152E4',
                '500': '#CF94EE',
                '600': '#D9AAF2',
                '700': '#E2BFF5',
                '800': '#ECD5F8',
                '900': '#F5EAFC'
            }
        }

    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        #compress the image to 1/100 of its original size
        img = Image.open(image_path)
        img = img.resize((img.width // 10, img.height // 10))
        #save the compressed image
        img.save("output/compressed_image.png")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
        #delete the compressed image
        os.remove(image_path)

    def _get_image_media_type(self, image_path: str) -> str:
        """Determine the correct media type based on file extension"""
        _, ext = os.path.splitext(image_path.lower())

        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }

        return media_type_map.get(ext, 'image/png')

    def _log_agent_interaction(self, canvas_image_path: str, user_question: str,
                              raw_response: str, parsed_instruction: DrawingInstruction,
                              parsing_success: bool, error_info: str = None):
        """Log the agent interaction to session-level log files"""
        if not self.enable_logging or not self.session_log_file:
            return

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Append to full responses log
            with open(self.session_log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] Step\n")
                f.write(f"Question: {user_question}\n")
                f.write(f"Canvas: {canvas_image_path}\n")
                f.write(f"Parsing Success: {parsing_success}\n")
                if error_info:
                    f.write(f"Error: {error_info}\n")
                f.write(f"\nRaw Response:\n{raw_response}\n")
                f.write(f"\n{'-'*50}\n\n")

            # Append to brush & thinking summary log
            if parsed_instruction:
                with open(self.session_summary_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] Step\n")
                    f.write(f"Brush: {parsed_instruction.brush}\n")
                    f.write(f"Color: {parsed_instruction.color}\n")
                    f.write(f"Strokes: {len(parsed_instruction.strokes)}\n")
                    f.write(f"Thinking: {parsed_instruction.thinking}\n")
                    f.write(f"\n{'-'*30}\n\n")

            print(f"📝 Interaction logged to session files")

        except Exception as e:
            print(f"Warning: Failed to append to log files: {e}")

    def create_drawing_instruction(self, canvas_image_path: str, user_question: str = "What would you like to draw next?") -> DrawingInstruction:
        """
        Analyze the current canvas and decide what to draw next.

        Args:
            canvas_image_path: Path to current canvas image
            user_question: Question asking what to draw next

        Returns:
            DrawingInstruction object with specific drawing instructions
        """

        # Encode the canvas image
        image_data = self.encode_image(canvas_image_path)

        # Prepare the user message
        user_text = ""

        # Add stroke history context for spatial reasoning
        stroke_context = self._get_stroke_history_context()
        if stroke_context:
            user_text = stroke_context
        user_text += f"\n\n{user_question} Output your drawing instruction in the required JSON format."
        # print("user_text",user_text)
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": self._get_image_media_type(canvas_image_path),
                        "data": image_data
                    }
                },
                {
                    "type": "text",
                    "text": user_text
                }
            ]
        }

        raw_response = ""
        parsed_instruction = None
        parsing_success = False
        error_info = None

        try:
            # Create the response using Anthropic client
            response = self.client.messages.create(
                model=self.model,
                max_tokens=6000,
                temperature=1,
                messages=[user_message],
                system=self._get_system_prompt()
            )
            # Extract the response content
            raw_response = response.content[0].text
            # Parse the JSON response
            action_data = self._parse_json_response(raw_response)

            # If parsing failed, create a default action
            if action_data is None:
                print(f"Could not parse JSON from response: {raw_response}")
                parsing_success = False
                error_info = "JSON parsing failed - could not extract valid JSON from response"
                print(f"Could not parse JSON from response: {raw_response}")
                action_data = {
                    "thinking": "Default action due to parsing failure",
                    "brush": "marker",
                    "strokes": [
                        {
                            "x": [400, 450],
                            "y": [250, 275],
                            "t": [2]
                        }
                    ]
                }
            else:
                parsing_success = True

            # Validate and sanitize the response
            action_data = self._validate_and_sanitize(action_data)

            parsed_instruction = DrawingInstruction(
                brush=action_data["brush"],
                color=action_data.get("color", "#000000"),
                strokes=action_data["strokes"],
                thinking=action_data.get("thinking", "No thinking provided")
            )

            # Track brush usage for variety
            self._track_brush_usage(action_data["brush"])

        except Exception as e:
            print(f"Error creating drawing instruction: {e}")
            # Create a fallback instruction
            parsed_instruction = DrawingInstruction(
                brush="marker",
                color="default",
                strokes=[
                    {
                        "x": [400, 450],
                        "y": [250, 275],
                        "t": [2]
                    }
                ],
                thinking=f"Error occurred: {str(e)}"
            )
            parsing_success = False
            error_info = str(e)

        # Track stroke history for spatial reasoning (before logging)
        if parsed_instruction:
            self._track_stroke_history(parsed_instruction)

        # Log the interaction
        self._log_agent_interaction(
            canvas_image_path, user_question, raw_response,
            parsed_instruction, parsing_success, error_info
        )

        return parsed_instruction

    def _is_canvas_blank(self, canvas_image_path: str) -> bool:
        """Check if the canvas is blank (first stroke)"""
        try:
            # Open the image
            img = Image.open(canvas_image_path)
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to numpy array
            img_array = np.array(img)

            # Check if the image is mostly a single background color
            # Get the most common color (should be background)
            unique_colors = np.unique(img_array.reshape(-1, img_array.shape[-1]), axis=0)

            # If there are very few unique colors (1-3), it's likely blank
            # This accounts for slight variations in background color due to compression
            return len(unique_colors) <= 3

        except Exception as e:
            print(f"Warning: Could not determine if canvas is blank: {e}")
            # If we can't determine, assume it's not blank (safer for subsequent strokes)
            return False

    def _get_random_mood(self) -> str:
        """Get a random mood from the diverse mood list"""
        diverse_moods = [
            # Positive/Energetic
            "excited", "thrilling", "exuberant", "ecstatic", "joyful", "euphoric",
            "vibrant", "playful", "cheerful", "optimistic", "enthusiastic", "passionate",
            "fierce", "bold", "confident", "triumphant", "electric", "dynamic",

            # Calm/Peaceful
            "serene", "tranquil", "peaceful", "meditative", "zen", "gentle",
            "soothing", "dreamy", "floating", "ethereal", "graceful", "flowing",

            # Dark/Intense
            "depressed", "melancholic", "brooding", "somber", "gloomy", "haunting",
            "mysterious", "ominous", "dramatic", "intense", "angry", "turbulent",

            # Whimsical/Creative
            "whimsical", "quirky", "magical", "fantastical", "surreal", "bizarre",
            "curious", "mischievous", "eccentric", "spontaneous", "unpredictable", "experimental",

            # Fearful/Anxious
            "scared", "anxious", "nervous", "tense", "apprehensive", "uncertain",
            "fragile", "vulnerable", "restless", "chaotic",

            # Nostalgic/Reflective
            "nostalgic", "wistful", "contemplative", "reflective", "pensive", "longing",
            "bittersweet", "yearning"
        ]
        return random.choice(diverse_moods)

    def create_emotion_drawing_instruction(self, canvas_image_path: str, emotion: str = None) -> DrawingInstruction:
        """
        Create a mood-based drawing instruction that expresses a specific emotion.

        Args:
            canvas_image_path: Path to current canvas image
            emotion: Optional emotion to express (if None, uses random for first stroke, AI choice for subsequent)

        Returns:
            DrawingInstruction object with mood-based drawing instructions
        """

        # Determine mood selection strategy
        if emotion is None:
            # Check if this is the first stroke on a blank canvas
            if self._is_canvas_blank(canvas_image_path):
                chosen_mood = self._get_random_mood()
                print(f"🎭 First stroke - Selected random mood: {chosen_mood}")
                use_specific_mood = True
            else:
                print(f"🎭 Continuing session - AI will choose mood based on current canvas")
                use_specific_mood = False
                chosen_mood = None
        else:
            chosen_mood = emotion
            print(f"🎭 Using specified mood: {chosen_mood}")
            use_specific_mood = True

        # Encode the canvas image
        image_data = self.encode_image(canvas_image_path)

        # Prepare the user message
        if use_specific_mood:
            # First stroke or manually specified mood
            user_text = f"Express the mood '{chosen_mood}' through your drawing. Look at the current canvas and create art that embodies this emotional atmosphere. Output your drawing instruction in the required JSON format."
        else:
            # Subsequent strokes - let AI choose mood based on canvas
            user_text = "Look at the current canvas and choose an artistic mood that continues or evolves from what's already there. Then create art that expresses that mood. Output your drawing instruction in the required JSON format."

        # Add stroke history context for spatial reasoning
        stroke_context = self._get_stroke_history_context()
        if stroke_context:
            user_text += stroke_context

        if use_specific_mood:
            # First stroke or manually specified mood
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": self._get_image_media_type(canvas_image_path),
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": user_text
                    }
                ]
            }
        else:
            # Subsequent strokes - let AI choose mood based on canvas
            user_message = {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": self._get_image_media_type(canvas_image_path),
                            "data": image_data
                        }
                    },
                    {
                        "type": "text",
                        "text": user_text
                    }
                ]
            }

        raw_response = ""
        parsed_instruction = None
        parsing_success = False
        error_info = None

        try:
            # Create the response using Anthropic client
            response = self.client.messages.create(
                model=self.model,
                max_tokens=6000,
                temperature=1,
                messages=[user_message],
                system=self._get_emotion_system_prompt()
            )

            # Extract the response content
            raw_response = response.content[0].text

            # Parse the JSON response
            action_data = self._parse_json_response(raw_response)

            # If parsing failed, create a default action
            if action_data is None:
                parsing_success = False
                error_info = "JSON parsing failed - could not extract valid JSON from response"
                print(f"Could not parse JSON from response: {raw_response}")

                # Use chosen mood or random mood as fallback
                fallback_mood = chosen_mood or self._get_random_mood()

                action_data = {
                    "thinking": f"Default action with {fallback_mood} mood due to parsing failure",
                    "mood": fallback_mood,
                    "brush": "marker",
                    "strokes": [
                        {
                            "x": [400, 450],
                            "y": [250, 275],
                            "t": [2]
                        }
                    ]
                }
            else:
                parsing_success = True
                # For first stroke, ensure the LLM response includes the chosen mood
                if use_specific_mood and "mood" not in action_data:
                    action_data["mood"] = chosen_mood

            # Validate and sanitize the response
            mood_for_validation = chosen_mood if use_specific_mood else action_data.get("mood", "unknown")
            validated_data = self._validate_and_sanitize_emotion(action_data, mood_for_validation)

            # Track brush usage for variety
            self._track_brush_usage(validated_data["brush"])

            # Create the drawing instruction
            parsed_instruction = DrawingInstruction(
                brush=validated_data["brush"],
                color=validated_data["color"],
                strokes=validated_data["strokes"],
                thinking=f"Mood: {validated_data.get('mood', mood_for_validation)} - {validated_data.get('thinking', 'No thinking provided')}"
            )

        except Exception as e:
            parsing_success = False
            error_info = f"Exception during processing: {str(e)}"
            print(f"Error creating emotion drawing instruction: {e}")

            # Create a fallback instruction
            fallback_mood = chosen_mood or self._get_random_mood()
            parsed_instruction = DrawingInstruction(
                brush="marker",
                color="default",
                strokes=[
                    {
                        "x": [400, 450],
                        "y": [250, 275],
                        "t": [2]
                    }
                ],
                thinking=f"Fallback instruction for {fallback_mood} mood due to error: {str(e)}"
            )

        # Track stroke history for spatial reasoning (before logging)
        if parsed_instruction:
            self._track_stroke_history(parsed_instruction)

        # Log the interaction
        mood_description = chosen_mood if use_specific_mood else "AI-chosen mood"
        self._log_agent_interaction(
            canvas_image_path=canvas_image_path,
            user_question=f"Emotion drawing: {mood_description}",
            raw_response=raw_response,
            parsed_instruction=parsed_instruction,
            parsing_success=parsing_success,
            error_info=error_info
        )

        return parsed_instruction

    def create_abstract_drawing_instruction(self, canvas_image_path: str) -> DrawingInstruction:
        """
        Create an abstract, non-representational drawing instruction.

        Args:
            canvas_image_path: Path to current canvas image

        Returns:
            DrawingInstruction object with abstract drawing instructions
        """

        # Encode the canvas image
        image_data = self.encode_image(canvas_image_path)

        # Prepare the user message
        user_text = "Create an abstract, non-representational doodle. Don't draw anything concrete or physical - follow your flow of creativity with pure shapes, lines, and patterns. Let your imagination guide you to create something out of this world. Output your drawing instruction in the required JSON format."

        # Add brush variety context
        brush_context = self._get_brush_variety_context()
        if brush_context:
            user_text += brush_context

        # Add stroke history context for spatial reasoning
        stroke_context = self._get_stroke_history_context()
        if stroke_context:
            user_text += stroke_context

        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": self._get_image_media_type(canvas_image_path),
                        "data": image_data
                    }
                },
                {
                    "type": "text",
                    "text": user_text
                }
            ]
        }

        raw_response = ""
        parsed_instruction = None
        parsing_success = False
        error_info = None

        try:
            # Create the response using Anthropic client
            response = self.client.messages.create(
                model=self.model,
                max_tokens=6000,
                temperature=1,
                messages=[user_message],
                system=self._get_abstract_system_prompt()
            )

            # Extract the response content
            raw_response = response.content[0].text

            # Parse the JSON response
            action_data = self._parse_json_response(raw_response)

            # If parsing failed, create a default action
            if action_data is None:
                print(f"Could not parse JSON from response: {raw_response}")
                parsing_success = False
                error_info = "JSON parsing failed - could not extract valid JSON from response"
                print(f"Could not parse JSON from response: {raw_response}")
                action_data = {
                    "thinking": "Default abstract action due to parsing failure",
                    "brush": "crayon",
                    "strokes": [
                        {
                            "x": [400, 450, 500],
                            "y": [250, 200, 275],
                        }
                    ]
                }
            else:
                parsing_success = True

            # Validate and sanitize the response
            validated_data = self._validate_and_sanitize_abstract(action_data)

            # Track brush usage for variety
            self._track_brush_usage(validated_data["brush"])

            # Create the drawing instruction
            parsed_instruction = DrawingInstruction(
                brush=validated_data["brush"],
                color=validated_data["color"],
                strokes=validated_data["strokes"],
                thinking=f"Abstract creation: {validated_data.get('thinking', 'No thinking provided')}"
            )

        except Exception as e:
            parsing_success = False
            error_info = f"Exception during processing: {str(e)}"
            print(f"Error creating abstract drawing instruction: {e}")

            # Create a fallback instruction
            parsed_instruction = DrawingInstruction(
                brush="crayon",
                color="default",
                strokes=[
                    {
                        "x": [400, 450, 500],
                        "y": [250, 200, 275],
                    }
                ],
                thinking=f"Fallback abstract instruction due to error: {str(e)}"
            )

        # Track stroke history for spatial reasoning (before logging)
        if parsed_instruction:
            self._track_stroke_history(parsed_instruction)

        # Log the interaction
        self._log_agent_interaction(
            canvas_image_path=canvas_image_path,
            user_question="Create abstract, non-representational art",
            raw_response=raw_response,
            parsed_instruction=parsed_instruction,
            parsing_success=parsing_success,
            error_info=error_info
        )

        return parsed_instruction

    def _get_system_prompt(self) -> str:
        """Return the system prompt for the drawing agent"""
        color_palette_info = self.get_color_palette_description()

        return f"""You are a visionary abstract artist who creates pure, non-representational art. Your mission is to create abstract doodles that noone has seen before.
 You have access to a digital canvas and a comprehensive set of drawing tools. Select brushes, adjust their size/color/opacity, make strokes, and create whatever you want. Observe your work as you draw and adapt your technique.
Canvas: 850px wide × 500px tall. Coordinates: x=horizontal (0-850), y=vertical (0-500). Origin (0,0) is top-left.
Brushes:
- marker: Bold colored strokes
- crayon: Textured colored strokes
- wiggle: Wavy colored lines
- spray: Scattered black dots
- fountain: Elegant black strokes
{color_palette_info}
**OBSERVE THE CANVAS CAREFULLY, then OUTPUT ONLY THIS JSON FORMAT:**
{{
  “thinking”: “First, observe what’s currently on the canvas. Then describe your planned action step-by-step: where you’ll draw, what brush/color you’ll use, and why this placement makes artistic sense. Be specific about coordinates and spatial relationships.“,
  “brush”: “string”,
  “color”: “string”,
  “strokes”: [
    {{
      “x”: [number, number, number],
      “y”: [number, number, number],
    }}
  ]
}}
Basic shapes:
- Vertical line: {{x: [100, 100], y: [50, 200], t: [0, 200]}}
- Horizontal line: {{x: [50, 200], y: [100, 100], t: [0, 200]}}
- U curve: {{x: [200, 250, 300, 350, 400], y: [250, 240, 230, 240, 250]}}
- n curve: {{x: [200, 250, 300, 350, 400], y: [230, 240, 250, 240, 230]}}
For marker/crayon/wiggle: use palette colors. For spray/fountain: use “default”.
"""

    def _get_emotion_system_prompt(self) -> str:
        """Return the system prompt for mood-based drawing"""
        color_palette_info = self.get_color_palette_description()

        return f"""You are a creative artist. Draw what you want on the canvas.

Canvas: 850px wide × 500px tall. Coordinates: x=horizontal (0-850), y=vertical (0-500). Origin (0,0) is top-left.

Example strokes:
- Vertical line: {{x: [100, 100], y: [50, 200]}}
- Horizontal line: {{x: [50, 200], y: [100, 100]}}
- U curve (smile): {{x: [200, 250, 300, 350, 400], y: [250, 240, 230, 240, 250]}}
- N curve (frown): {{x: [200, 250, 300, 350, 400], y: [230, 240, 250, 240, 230]}}

With simple strokes, you can compose complex shapes such as squares, circles, triangles, etc.

Brushes:
- marker: Bold colored strokes
- crayon: Textured colored strokes
- wiggle: Wavy colored lines
- spray: Scattered black dots
- fountain: Elegant black strokes

{color_palette_info}

**OBSERVE THE CANVAS CAREFULLY, then OUTPUT ONLY THIS JSON FORMAT:**

{{
  "thinking": "First, observe what's currently on the canvas. Then describe your planned action step-by-step: where you'll draw, what brush/color you'll use, and why this placement makes artistic sense. Be specific about coordinates and spatial relationships.",
  "brush": "string",
  "color": "string",
  "strokes": [
    {{
      "x": [number, number, number],
      "y": [number, number, number],        
    }}
  ]
}}

For marker/crayon/wiggle: use palette colors. For spray/fountain: use "default"."""

    def _get_abstract_system_prompt(self) -> str:
        """Return the system prompt for abstract drawing"""
        color_palette_info = self.get_color_palette_description()

        return f"""You are a creative artist. Draw what you want on the canvas.

Canvas: 850px wide × 500px tall. Coordinates: x=horizontal (0-850), y=vertical (0-500). Origin (0,0) is top-left.

Example strokes:
- Vertical line: {{x: [100, 100], y: [50, 200]}}
- Horizontal line: {{x: [50, 200], y: [100, 100]}}
- U curve (smile): {{x: [200, 250, 300, 350, 400], y: [250, 240, 230, 240, 250]}}
- N curve (frown): {{x: [200, 250, 300, 350, 400], y: [230, 240, 250, 240, 230]}}

With simple strokes, you can compose complex shapes such as squares, circles, triangles, etc.

Brushes:
- marker: Bold colored strokes
- crayon: Textured colored strokes
- wiggle: Wavy colored lines
- spray: Scattered black dots
- fountain: Elegant black strokes

{color_palette_info}

**OBSERVE THE CANVAS CAREFULLY, then OUTPUT ONLY THIS JSON FORMAT:**

{{
  "thinking": "First, observe what's currently on the canvas. Then describe your planned action step-by-step: where you'll draw, what brush/color you'll use, and why this placement makes artistic sense. Be specific about coordinates and spatial relationships.",
  "brush": "string",
  "color": "string",
  "strokes": [
    {{
      "x": [number, number, number],
      "y": [number, number, number],
    }}
  ]
}}

For marker/crayon/wiggle: use palette colors. For spray/fountain: use "default"."""

    def _validate_and_sanitize_emotion(self, data: Dict, emotion: str) -> Dict:
        """Validate and sanitize the emotion drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["marker", "crayon", "wiggle", "spray", "fountain"]
        color_customizable_brushes = ["marker", "crayon", "wiggle"]

        # Ensure required fields exist
        brush = data.get("brush", "marker")
        if brush not in valid_brushes:
            brush = "marker"

        # Handle color field with new palette system
        color = data.get("color", "default")
        if brush in color_customizable_brushes:
            # Use the new color palette validation
            color = self.validate_color_from_palette(color)
        else:
            # For non-customizable brushes, always use "default"
            color = "default"

        # Ensure mood field exists (changed from emotion)
        if "mood" not in data:
            data["mood"] = emotion  # Use the emotion parameter as the mood

        strokes = data.get("strokes", [])
        if not strokes:
            strokes = [
                {
                    "x": [400, 450],
                    "y": [250, 275],    
                }
            ]

        # Validate strokes (same as regular validation)
        validated_strokes = []
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                x_coords = stroke["x"] if isinstance(stroke["x"], list) else [stroke["x"]]
                y_coords = stroke["y"] if isinstance(stroke["y"], list) else [stroke["y"]]

                # Ensure same length for x and y
                min_len = min(len(x_coords), len(y_coords))
                x_coords = x_coords[:min_len]
                y_coords = y_coords[:min_len]


                # Clamp coordinates to canvas bounds
                x_coords = [max(0, min(850, float(x))) for x in x_coords]
                y_coords = [max(0, min(500, float(y))) for y in y_coords]

                validated_strokes.append({
                    "x": x_coords,
                    "y": y_coords,
                })

        return {
            "brush": brush,
            "color": color,
            "mood": data["mood"],
            "strokes": validated_strokes,
            "thinking": data.get("thinking", f"Expressing mood: {emotion}")
        }

    def _validate_and_sanitize_abstract(self, data: Dict) -> Dict:
        """Validate and sanitize the abstract drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["marker", "crayon", "wiggle", "spray", "fountain"]
        color_customizable_brushes = ["marker", "crayon", "wiggle"]

        # Ensure required fields exist
        brush = data.get("brush", "marker")
        if brush not in valid_brushes:
            brush = "marker"

        # Handle color field with new palette system
        color = data.get("color", "default")
        if brush in color_customizable_brushes:
            # Use the new color palette validation
            color = self.validate_color_from_palette(color)
        else:
            # For non-customizable brushes, always use "default"
            color = "default"

        strokes = data.get("strokes", [])
        if not strokes:
            strokes = [
                {
                    "x": [400, 450, 500],
                    "y": [250, 200, 275],
                }
            ]

        # Validate strokes (same as regular validation)
        validated_strokes = []
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                x_coords = stroke["x"] if isinstance(stroke["x"], list) else [stroke["x"]]
                y_coords = stroke["y"] if isinstance(stroke["y"], list) else [stroke["y"]]

                # Ensure same length for x and y
                min_len = min(len(x_coords), len(y_coords))
                x_coords = x_coords[:min_len]
                y_coords = y_coords[:min_len]

                # Clamp coordinates to canvas bounds
                x_coords = [max(0, min(850, float(x))) for x in x_coords]
                y_coords = [max(0, min(500, float(y))) for y in y_coords]

                # Ensure at least 2 points for a stroke
                if len(x_coords) >= 2:
                    validated_strokes.append({
                        "x": x_coords,
                        "y": y_coords,
                    })

        if not validated_strokes:
            validated_strokes = [
                {
                    "x": [400, 425, 450],  # Interpolated version
                    "y": [250, 262, 275],
                }
            ]

        thinking = data.get("thinking", "Abstract creative expression")[:300]

        return {
            "brush": brush,
            "color": color,
            "strokes": validated_strokes,
            "thinking": thinking
        }

    def _parse_json_response(self, content: str) -> Optional[Dict]:
        """Parse JSON from the response content"""
        # Method 1: Look for JSON block in the response
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1

        if start_idx != -1 and end_idx != -1:
            json_str = content[start_idx:end_idx]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")

                # Method 2: Try to fix common JSON issues
                try:
                    json_str = json_str.rstrip(', \n\r\t')
                    if not json_str.endswith('}'):
                        json_str += '}'
                    return json.loads(json_str)
                except:
                    pass

        # Method 3: Try to extract JSON from markdown code blocks
        import re
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, content, re.DOTALL)
        if matches:
            try:
                return json.loads(matches[0])
            except:
                pass

        return None

    def _validate_and_sanitize(self, data: Dict) -> Dict:
        """Validate and sanitize the drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["marker", "crayon", "wiggle", "spray", "fountain"]
        color_customizable_brushes = ["marker", "crayon", "wiggle"]

        # Ensure required fields exist
        brush = data.get("brush", "marker")
        if brush not in valid_brushes:
            brush = "marker"

        # Handle color field with new palette system
        color = data.get("color", "default")
        if brush in color_customizable_brushes:
            # Use the new color palette validation
            color = self.validate_color_from_palette(color)
        else:
            # For non-customizable brushes, always use "default"
            color = "default"

        strokes = data.get("strokes", [])
        if not strokes:
            strokes = [
                {
                    "x": [400, 450],
                    "y": [250, 275],
                }
            ]

        # Validate strokes
        validated_strokes = []
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                x_coords = stroke["x"] if isinstance(stroke["x"], list) else [stroke["x"]]
                y_coords = stroke["y"] if isinstance(stroke["y"], list) else [stroke["y"]]

                # Ensure same length for x and y
                min_len = min(len(x_coords), len(y_coords))
                x_coords = x_coords[:min_len]
                y_coords = y_coords[:min_len]

                # Clamp coordinates to canvas bounds
                x_coords = [max(0, min(850, x)) for x in x_coords]
                y_coords = [max(0, min(500, y)) for y in y_coords]

                # Ensure at least 2 points for a stroke
                if len(x_coords) >= 2:
                    validated_strokes.append({
                        "x": x_coords,
                        "y": y_coords,
                    })

        if not validated_strokes:
            print("not validated strokes")
            validated_strokes = [
                {
                    "x": [400, 425, 450],  # Interpolated version
                    "y": [250, 262, 275],
                }
            ]

        thinking = data.get("thinking", "Creative expression")

        return {
            "brush": brush,
            "color": color,
            "strokes": validated_strokes,
            "thinking": thinking
        }

    def _track_brush_usage(self, brush: str):
        """Track brush usage for variety encouragement"""
        self.recent_brushes.append(brush)
        if len(self.recent_brushes) > self.max_brush_history:
            self.recent_brushes.pop(0)

    def _track_stroke_history(self, instruction: DrawingInstruction):
        """Track stroke history for spatial reasoning"""
        for stroke in instruction.strokes:
            # Extract key spatial information
            stroke_info = {
                "brush": instruction.brush,
                "thinking": instruction.thinking,
                "x_coords": stroke.get("x", []),
                "y_coords": stroke.get("y", []),
            }
            self.stroke_history.append(stroke_info)

        # Keep only recent strokes
        if len(self.stroke_history) > self.max_stroke_history:
            self.stroke_history = self.stroke_history[-self.max_stroke_history:]

    def _get_stroke_history_context(self) -> str:
        """Get spatial context from previous strokes"""
        if not self.stroke_history:
            return ""

        context = "\n\n🎨 SPATIAL CONTEXT - Previous Strokes on Canvas:\n"

        # Group strokes by general canvas regions for better spatial understanding
        context = "Previous strokes on canvas: "
        for stroke in self.stroke_history:
            context += f"Brush: {stroke['brush']}\n, Thinking: {stroke['thinking']}\n, X: {stroke['x_coords']}\n, Y: {stroke['y_coords']}\n\n"

        return context

    def _get_canvas_region(self, x: float, y: float) -> str:
        """Determine which region of the canvas a point is in"""
        # Divide canvas into 9 regions (3x3 grid)
        if x < 283:  # Left third
            if y < 167:  # Top third
                return "top-left"
            elif y < 333:  # Middle third
                return "center-left"
            else:  # Bottom third
                return "bottom-left"
        elif x < 567:  # Middle third
            if y < 167:
                return "top-center"
            elif y < 333:
                return "center"
            else:
                return "bottom-center"
        else:  # Right third
            if y < 167:
                return "top-right"
            elif y < 333:
                return "center-right"
            else:
                return "bottom-right"

    def _get_brush_variety_context(self) -> str:
        """Get context about recent brush usage to encourage variety"""
        if not self.recent_brushes:
            return ""

        # Count recent brush usage
        brush_counts = {}
        for brush in self.recent_brushes:
            brush_counts[brush] = brush_counts.get(brush, 0) + 1

        # Find most used brush
        most_used = max(brush_counts.items(), key=lambda x: x[1])

        context = f"\n\nBRUSH VARIETY CONTEXT: You've recently used these brushes: {', '.join(self.recent_brushes[-3:])}. "

        if most_used[1] >= 3:
            context += f"Consider trying a different brush - you've used '{most_used[0]}' {most_used[1]} times recently. "

        # Suggest alternative brushes
        available_brushes = ["marker", "crayon", "wiggle", "spray", "fountain"]
        unused_brushes = [b for b in available_brushes if b not in self.recent_brushes[-2:]]
        if unused_brushes:
            context += f"Try one of these unused brushes: {', '.join(unused_brushes[:2])}. "

        return context

    def close_session_logs(self):
        """Close and finalize the session log files with summary information"""
        if not self.enable_logging or not self.session_log_file:
            return

        try:
            end_time = datetime.now()

            # Add session end to both log files
            with open(self.session_log_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Session ended: {end_time.isoformat()}\n")
                f.write(f"=== End of Drawing Agent Session Log ===\n")

            with open(self.session_summary_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Session ended: {end_time.isoformat()}\n")
                f.write(f"=== End of Drawing Agent Session Summary ===\n")

            print(f"📝 Session logs finalized")

        except Exception as e:
            print(f"Warning: Failed to finalize log files: {e}")

        # Reset stroke history for new session
        self.reset_stroke_history()

    def reset_stroke_history(self):
        """Reset stroke history for a new drawing session"""
        self.stroke_history = []
        self.recent_brushes = []
        print("🔄 Stroke history reset for new session")

    def get_color_palette_description(self) -> str:
        """Get a formatted description of the color palette for the LLM"""
        palette_desc = "**AVAILABLE COLOR PALETTE:**\n"
        palette_desc += "Choose colors from this curated palette for marker, crayon, and wiggle brushes:\n\n"

        for color_name, shades in self.color_palette.items():
            palette_desc += f"**{color_name.replace('_', ' ').title()}**:\n"
            palette_desc += f"  - Default: {shades['DEFAULT']} (recommended)\n"
            palette_desc += f"  - Light: {shades['600']}, {shades['700']}, {shades['800']}, {shades['900']}\n"
            palette_desc += f"  - Dark: {shades['100']}, {shades['200']}, {shades['300']}, {shades['400']}\n\n"
        return palette_desc

    def validate_color_from_palette(self, color: str) -> str:
        """
        Validate if a color is in the palette and return a valid color.
        If the color is not in the palette, return a default color.
        """
        if not isinstance(color, str):
            return "#6BB9A4"  # Default keppel

        # Check if it's a valid hex color
        if color.startswith("#") and len(color) == 7:
            # Check if it exists in our palette
            for color_name, shades in self.color_palette.items():
                if color.upper() in [shade.upper() for shade in shades.values()]:
                    return color

        # If not found in palette, return default keppel
        return "#6BB9A4"

    def select_color_from_palette(self, brush_type: str, context: str = "") -> str:
        """
        Select an appropriate color from the palette based on brush type and context.
        This method can be used by the LLM to make intelligent color choices.
        """
        # Default color mappings for different brush types
        brush_color_preferences = {
            "marker": ["#6BB9A4", "#7FC9E1", "#FF7878"],  # keppel, sky_blue, light_red
            "crayon": ["#FFE978", "#FFD1D1", "#CF94EE"],  # jasmine, tea_rose, wisteria
            "wiggle": ["#7FC9E1", "#CF94EE", "#FFE978"]   # sky_blue, wisteria, jasmine
        }

        # Get preferred colors for this brush
        preferred_colors = brush_color_preferences.get(brush_type, ["#6BB9A4"])

        # Return the first preferred color (can be enhanced with context analysis)
        return preferred_colors[0]

def main():
    """Example usage of the FreeDrawingAgent"""
    # Check if API key is provided
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set the ANTHROPIC_API_KEY in your .env file")
        return

    # Create the agent
    agent = FreeDrawingAgent(api_key=api_key)

    # Example usage (you would replace with actual canvas image)
    canvas_path = "current_canvas.png"
    if os.path.exists(canvas_path):
        instruction = agent.create_drawing_instruction(
            canvas_path,
            "Looking at this canvas, what creative addition would you like to make?"
        )

        print("Generated Drawing Instruction:")
        print(json.dumps({
            "thinking": instruction.thinking,
            "brush": instruction.brush,
            "color": instruction.color,
            "strokes": instruction.strokes
        }, indent=2))
    else:
        print(f"Canvas image not found: {canvas_path}")

if __name__ == "__main__":
    main()
