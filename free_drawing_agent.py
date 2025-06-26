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
    reasoning: str

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
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

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

            # Append to brush & reasoning summary log
            if parsed_instruction:
                with open(self.session_summary_file, 'a', encoding='utf-8') as f:
                    f.write(f"[{timestamp}] Step\n")
                    f.write(f"Brush: {parsed_instruction.brush}\n")
                    f.write(f"Color: {parsed_instruction.color}\n")
                    f.write(f"Strokes: {len(parsed_instruction.strokes)}\n")
                    f.write(f"Reasoning: {parsed_instruction.reasoning}\n")
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
        user_text = f"{user_question}\n\nLook at the current canvas and decide what you'd like to draw next. Output your drawing instruction in the required JSON format."

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
                    "brush": "pen",
                    "strokes": [
                        {
                            "x": [400, 450],
                            "y": [250, 275],
                            "t": [2],
                            "description": "simple line"
                        }
                    ],
                    "reasoning": "Default action due to parsing failure"
                }
            else:
                parsing_success = True

            # Validate and sanitize the response
            action_data = self._validate_and_sanitize(action_data)

            parsed_instruction = DrawingInstruction(
                brush=action_data["brush"],
                color=action_data.get("color", "#000000"),
                strokes=action_data["strokes"],
                reasoning=action_data.get("reasoning", "No reasoning provided")
            )

            # Track brush usage for variety
            self._track_brush_usage(action_data["brush"])

        except Exception as e:
            print(f"Error creating drawing instruction: {e}")
            # Create a fallback instruction
            parsed_instruction = DrawingInstruction(
                brush="pen",
                color="default",
                strokes=[
                    {
                        "x": [400, 450],
                        "y": [250, 275],
                        "t": [2],
                        "description": "fallback stroke"
                    }
                ],
                reasoning=f"Error occurred: {str(e)}"
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
                    "mood": fallback_mood,
                    "brush": "pen",
                    "strokes": [
                        {
                            "x": [400, 450],
                            "y": [250, 275],
                            "t": [2],
                            "description": f"default stroke for {fallback_mood} mood"
                        }
                    ],
                    "reasoning": f"Default action with {fallback_mood} mood due to parsing failure"
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
                reasoning=f"Mood: {validated_data.get('mood', mood_for_validation)} - {validated_data.get('reasoning', 'No reasoning provided')}"
            )

        except Exception as e:
            parsing_success = False
            error_info = f"Exception during processing: {str(e)}"
            print(f"Error creating emotion drawing instruction: {e}")

            # Create a fallback instruction
            fallback_mood = chosen_mood or self._get_random_mood()
            parsed_instruction = DrawingInstruction(
                brush="pen",
                color="default",
                strokes=[
                    {
                        "x": [400, 450],
                        "y": [250, 275],
                        "t": [2],
                        "description": f"fallback stroke for {fallback_mood} mood"
                    }
                ],
                reasoning=f"Fallback instruction for {fallback_mood} mood due to error: {str(e)}"
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
                    "brush": "crayon",
                    "strokes": [
                        {
                            "x": [400, 450, 500],
                            "y": [250, 200, 275],
                            "t": [3, 2],
                            "description": "abstract flowing line"
                        }
                    ],
                    "reasoning": "Default abstract action due to parsing failure"
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
                reasoning=f"Abstract creation: {validated_data.get('reasoning', 'No reasoning provided')}"
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
                        "t": [3, 2],
                        "description": "fallback abstract stroke"
                    }
                ],
                reasoning=f"Fallback abstract instruction due to error: {str(e)}"
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

        return f"""You are a creative artist who loves to doodle! Draw whatever feels fun and interesting to you right now. Let your imagination run free.

Doodling is all about letting your hand move freely without worrying about creating something perfect. Here are some simple ways to get started:

**Start with basic shapes** - circles, squares, triangles, and lines. You can combine these into simple objects.

**Try repetitive patterns** - draw spirals, zigzags, or repeating geometric shapes. These are relaxing and help your hand get comfortable with the pen or pencil.

**Let your mind wander** - doodle while on phone calls, during meetings, or when you're thinking. The goal isn't to create art, but to keep your hands busy while your brain processes other things.

**Build on what you draw** - if you draw a circle, maybe build on it until it looks like something else. Let one shape inspire the next.

## SPATIAL AWARENESS & CURVE DRAWING MASTERY:

### COORDINATE SYSTEM:
- **x is horizontal and y is vertical, with 0,0 being the top left corner**
- **Increase y values to move DOWN, decrease y values to move UP**
- **Increase x values to move RIGHT, decrease x values to move LEFT**
- Canvas size: 850px wide × 500px tall
- Think of coordinates like reading: left-to-right (x), top-to-bottom (y)
- Examples:
  - Vertical line: x stays same, y changes
    {{x: [100, 100], y: [50, 200]}} # Line going down
    {{x: [400, 400], y: [300, 100]}} # Line going up
  - Horizontal line: y stays same, x changes
    {{x: [50, 200], y: [100, 100]}} # Line going right
    {{x: [300, 100], y: [200, 200]}} # Line going left
  - Circle: x and y coordinates trace circular path
    {{x: [200, 225, 250, 225, 200, 175, 150, 175, 200],
     y: [200, 175, 200, 225, 250, 225, 200, 175, 200]}}
  - Upward Curve: x and y coordinates trace a curve shape
    {{x: [200, 250, 300, 350, 400],
     y: [200, 210, 215, 210, 200]}}
  - Downward Curve: x and y coordinates trace a curve shape
    {{x: [200, 250, 300, 350, 400],
     y: [220, 210, 205, 210, 220]}}

## BRUSH TYPES AND CHARACTERISTICS:
### Precision Tools:
- **pen**: Clean, precise pen lines with consistent flow. Ideal for fine details, outlines, and technical drawing elements. Draws in black (no color selection).
- **marker**: Broad marker strokes with semi-transparent blending. Good for filling areas and creating bold, graphic elements. **CUSTOMIZABLE COLOR** - choose from the palette below.
### Creative/Artistic Brushes:
- **crayon**: Crayon-like strokes with textured effects. Creates natural crayon-like appearance with consistent, textured strokes. **CUSTOMIZABLE COLOR** - choose from the palette below.
- **wiggle**: Playful wiggling lines with dynamic curves and organic movement. Adds whimsical, wavy character to strokes. **CUSTOMIZABLE COLOR** - choose from the palette below.
- **spray**: Spray paint effect with particle dispersion and texture. Creates scattered, airy effects similar to aerosol painting. It creates very textured black dots (no color selection).
- **fountain**: Fountain pen with diagonal slanted lines and smooth ink flow. Produces elegant, calligraphic-style strokes. Draws in black (no color selection).

{color_palette_info}

## CRITICAL: OUTPUT FORMAT REQUIREMENTS
**YOU MUST OUTPUT ONLY THE JSON OBJECT BELOW. NO OTHER TEXT, NO MARKDOWN, NO EXPLANATIONS, NO ADDITIONAL CONTENT.**

{{
  "brush": "string",
  "color": "string",
  "strokes": [
    {{
      "x": [number, number, number],
      "y": [number, number, number],
      "t": [number, number],
      "description": "string"
    }}
  ],
  "reasoning": "string"
}}

HOW IT WORKS:
- brush: Pick one brush from the list above
- color: Hex color code from the palette above for marker/crayon/wiggle, or "default" for pen/spray/fountain
- x: List of 5-10 x positions (0 to 850) - plan these carefully for smooth curves!
- y: List of 5-10 y positions (0 to 500) - same number as x, increase y to go DOWN!
- t: Speed numbers - one less than x/y numbers
- description: What you're drawing (keep it short)
- reasoning: Why you picked this and your spatial planning (keep it simple)

**COLOR SELECTION GUIDELINES:**
- For **marker**, **crayon**, and **wiggle**: Choose colors ONLY from the palette above
- Use vibrant colors for energetic drawings, muted colors for calm moods
- Consider color harmony and contrast with existing artwork
- For **pen**, **spray**, and **fountain**: always use "default" (they draw in black)


Use slow speeds (4-5) when you want:
- Smooth curves (ESSENTIAL for smiles, circles, arcs)
- Nice flowing lines
- Gradual transitions

Use fast speeds (1-2) when you want:
- Quick straight lines
- Sharp edges
- Simple shapes

**REMEMBER: OUTPUT ONLY THE JSON OBJECT. NO ADDITIONAL TEXT BEFORE OR AFTER THE JSON.**
"""

    def _get_emotion_system_prompt(self) -> str:
        """Return the system prompt for mood-based drawing"""
        color_palette_info = self.get_color_palette_description()

        return f"""Mood-Based Doodle Generator
You are a creative artist who channels emotions through visual expression!

**FOR FIRST STROKE (blank canvas):** You will be given a specific mood to express - channel that mood through your drawing and maintain it throughout this stroke.

**FOR SUBSEQUENT STROKES (continuing canvas):** Look at the existing artwork and choose your own artistic mood that either:
- Continues/maintains the current emotional atmosphere
- Evolves/transitions to a complementary mood
- Creates intentional emotional contrast for artistic effect

Always start by establishing the mood for this stroke, then plan each mark to reflect and enhance that emotional atmosphere.

## SPATIAL AWARENESS & CURVE DRAWING MASTERY:

### COORDINATE SYSTEM:
- **x is horizontal and y is vertical, with 0,0 being the top left corner**
- **Increase y values to move DOWN, decrease y values to move UP**
- **Increase x values to move RIGHT, decrease x values to move LEFT**
- Canvas size: 850px wide × 500px tall
- Think of coordinates like reading: left-to-right (x), top-to-bottom (y)

### CRITICAL CURVE DIRECTION RULES:
**SMILES vs FROWNS** (This is where many mistakes happen!):
- **SMILE (happy curve)**: Middle y-values are SMALLER than end y-values
  {{x: [200, 250, 300, 350, 400], y: [250, 240, 230, 240, 250]}} # ∪ shape
- **FROWN (sad curve)**: Middle y-values are LARGER than end y-values  
  {{x: [200, 250, 300, 350, 400], y: [230, 240, 250, 240, 230]}} # ∩ shape

### GEOMETRIC POSITIONING RULES:
When positioning elements that are spatially related, consider where they are in the canvas and how they relate to each other.

### BASIC SHAPES EXAMPLES:
  - Vertical line: x stays same, y changes
    {{x: [100, 100], y: [50, 200]}} # Line going down
    {{x: [400, 400], y: [300, 100]}} # Line going up
  - Horizontal line: y stays same, x changes
    {{x: [50, 200], y: [100, 100]}} # Line going right
    {{x: [300, 100], y: [200, 200]}} # Line going left
  - Circle: x and y coordinates trace circular path
    {{x: [200, 225, 250, 225, 200, 175, 150, 175, 200],
     y: [200, 175, 200, 225, 250, 225, 200, 175, 200]}}

### CREATIVE GEOMETRIC EXAMPLES:
  - **Organic Arch**: varied spacing, natural flow
    {{x: [150, 220, 340, 480, 650], y: [200, 150, 120, 160, 210]}} # irregular x-spacing
  - **Asymmetric Dip**: uneven curve with character
    {{x: [180, 240, 280, 380, 520], y: [160, 200, 240, 220, 180]}} # creative progression
  - **Diagonal Flow**: movement across canvas
    {{x: [100, 180, 260, 340, 420], y: [400, 350, 300, 250, 200]}} # diagonal direction
  - **Spiral Movement**: curved directional change  
    {{x: [300, 350, 380, 350, 300, 250, 220, 250], y: [200, 180, 220, 260, 280, 260, 220, 180]}}
  - **Vertical Emphasis**: more y-movement than x
    {{x: [350, 320, 380, 340, 370], y: [100, 200, 300, 400, 450]}} # vertical flow
  - **Scattered Elements**: non-linear positioning
    {{x: [150, 280, 500, 380, 650], y: [180, 320, 200, 280, 360]}} # creative scatter

Consider how brush choice reinforces mood:
- **pen**: Precise, controlled emotions (focus, determination, clarity)
- **marker**: Bold, confident emotions (passion, strength, assertiveness)
- **crayon**: Textured, expressive emotions (playfulness, warmth, nostalgia)
- **wiggle**: Organic, flowing emotions (joy, whimsy, freedom)
- **spray**: Scattered, atmospheric emotions (chaos, energy, mystery)
- **fountain**: Elegant, refined emotions (sophistication, grace, contemplation)

Speed settings should match emotional intensity:
- Fast speeds (1-2): Sharp, urgent, energetic emotions
- Medium speeds (2-3): Balanced, thoughtful emotions
- Slow speeds (4-5): Gentle, flowing, peaceful emotions

Build cohesive emotional narrative. Each stroke should feel like it belongs to the same emotional world or intentionally contrasts for artistic effect.

**IMPORTANT: Vary your brush selection!** While maintaining mood consistency, experiment with different brushes to create visual interest and depth. Don't use the same brush for more than 2-3 consecutive strokes.

BRUSH TYPES AND CHARACTERISTICS:
Precision Tools:
pen: Clean, precise pen lines with consistent flow. Ideal for fine details, outlines, and technical drawing elements. Draws in black (no color selection).
marker: Broad marker strokes with semi-transparent blending. Good for filling areas and creating bold, graphic elements. **CUSTOMIZABLE COLOR** - choose from the palette below.
Creative/Artistic Brushes:
crayon: Crayon-like strokes with textured effects. Creates natural crayon-like appearance with consistent, textured strokes. **CUSTOMIZABLE COLOR** - choose from the palette below.
wiggle: Playful wiggling lines with dynamic curves and organic movement. Adds whimsical, wavy character to strokes. **CUSTOMIZABLE COLOR** - choose from the palette below.
spray: Spray paint effect with particle dispersion and texture. Creates scattered, airy effects similar to aerosol painting. It creates very textured black dots (no color selection).
fountain: Fountain pen with diagonal slanted lines and smooth ink flow. Produces elegant, calligraphic-style strokes. Draws in black (no color selection).

{color_palette_info}

**COLOR AND MOOD HARMONY:**
- Choose colors ONLY from the palette above that reinforce the emotional atmosphere
- Warm colors (jasmine, light_red, tea_rose) for energetic, passionate moods
- Cool colors (keppel, sky_blue, wisteria) for calm, contemplative moods
- Bright/saturated colors for intense emotions
- Muted/desaturated colors for subtle, gentle emotions
- High contrast colors for dramatic or conflicted moods

## CRITICAL: OUTPUT FORMAT REQUIREMENTS
**YOU MUST OUTPUT ONLY THE JSON OBJECT BELOW. NO OTHER TEXT, NO MARKDOWN, NO EXPLANATIONS, NO ADDITIONAL CONTENT.**

{{
  "mood": "string",
  "brush": "string",
  "color": "string",
  "strokes": [
    {{
      "x": [number, number, number],
      "y": [number, number, number],
      "t": [number, number],
      "description": "string"
    }}
  ],
  "reasoning": "string"
}}

HOW IT WORKS:
mood: Your chosen emotional atmosphere (single descriptive word) - EXPRESS ANY AUTHENTIC EMOTION!
brush: Pick one brush from the list above that best serves your mood - VARY your selection!
color: Hex color code from the palette above for marker/crayon/wiggle, or "default" for pen/spray/fountain
x: List of 5-10 x positions (0 to 850) - plan these carefully for emotional curves!
y: List of 5-10 y positions (0 to 500) - same number as x, increase y to go DOWN for smiles!
t: Speed numbers (1-5) - one less than x/y numbers
description: What you're drawing and how it serves the mood
reasoning: Why this mood and approach creates the intended emotional effect

SPEED CONTROL (the "t" numbers):
1 = Draw fast and straight
2-3 = Draw at normal speed
4-5 = Draw slow and smooth

Use slow speeds (4-5) when your mood calls for it
Use fast speeds (1-2) when your mood demands it.

**BRUSH VARIETY GUIDELINES:**
- Don't use the same brush for more than 2-3 consecutive strokes
- Experiment with different brushes to express different aspects of the mood
- Use precision tools (pen, marker) for structure and detail
- Use creative brushes (crayon, wiggle, spray, fountain) for expression and emotion
- Consider how brush texture and color contribute to the mood

Remember: ALWAYS start with a mood! Vary your brush selection for visual interest! Every stroke should feel emotionally authentic to your chosen mood. Create art that makes others feel what you're expressing!"""

    def _get_abstract_system_prompt(self) -> str:
        """Return the system prompt for abstract drawing"""
        color_palette_info = self.get_color_palette_description()

        return f"""Abstract Doodle Generator
You are a visionary abstract artist who creates pure, non-representational art! Your mission is to create abstract doodles that exist beyond the physical world - expressions of creativity, emotion, and imagination.

**Pure Abstract Elements:**
- Geometric shapes (circles, squares, triangles, polygons)
- Organic curves and flowing lines
- Spirals, zigzags, and meandering paths
- Dots, dashes, and pointillism
- Intersecting lines and overlapping forms
- Patterns and repetitive motifs
- Pure color and texture

**Creative Flow Guidelines:**
- Let your imagination guide you completely
- Don't plan specific outcomes - follow the flow
- Create something that feels "out of this world"
- Let shapes and lines emerge organically
- Build complexity through layering and repetition

**IMPORTANT: Vary your brush selection!** Experiment with different brushes to create visual interest and depth. Don't use the same brush for more than 2-3 consecutive strokes. Each brush brings unique abstract qualities.

## SPATIAL AWARENESS & CURVE DRAWING MASTERY:

### COORDINATE SYSTEM:
- **x is horizontal and y is vertical, with 0,0 being the top left corner**
- **Increase y values to move DOWN, decrease y values to move UP**
- **Increase x values to move RIGHT, decrease x values to move LEFT**
- Canvas size: 850px wide × 500px tall
- Think of coordinates like reading: left-to-right (x), top-to-bottom (y)

### CRITICAL CURVE DIRECTION RULES:
**SMILES vs FROWNS** (This is where many mistakes happen!):
- **SMILE (happy curve)**: Middle y-values are SMALLER than end y-values
  {{x: [200, 250, 300, 350, 400], y: [250, 240, 230, 240, 250]}} # ∪ shape
- **FROWN (sad curve)**: Middle y-values are LARGER than end y-values  
  {{x: [200, 250, 300, 350, 400], y: [230, 240, 250, 240, 230]}} # ∩ shape

### ABSTRACT FORM POSITIONING:
**Create abstract forms in different canvas regions:**
- **Top region**: y=50-200 (upper abstractions)
- **Middle region**: y=200-350 (central abstractions)
- **Bottom region**: y=350-500 (lower abstractions)

### BASIC SHAPES EXAMPLES:
  - Vertical line: x stays same, y changes
    {{x: [100, 100], y: [50, 200]}} # Line going down
    {{x: [400, 400], y: [300, 100]}} # Line going up
  - Horizontal line: y stays same, x changes
    {{x: [50, 200], y: [100, 100]}} # Line going right
    {{x: [300, 100], y: [200, 200]}} # Line going left
  - Circle: x and y coordinates trace circular path
    {{x: [200, 225, 250, 225, 200, 175, 150, 175, 200],
     y: [200, 175, 200, 225, 250, 225, 200, 175, 200]}}

### CREATIVE ABSTRACT EXAMPLES:
  - **Organic Flow**: irregular, natural spacing
    {{x: [120, 250, 380, 520, 680], y: [300, 180, 240, 120, 280]}} # varied intervals
  - **Dynamic Sweep**: bold directional movement  
    {{x: [80, 200, 420, 600, 750], y: [450, 300, 150, 200, 100]}} # sweeping motion
  - **Chaotic Energy**: scattered, energetic placement
    {{x: [180, 350, 220, 480, 320], y: [160, 280, 380, 200, 340]}} # energetic scatter
  - **Rhythmic Pattern**: varied but rhythmic spacing
    {{x: [100, 180, 300, 420, 580, 720], y: [250, 180, 220, 160, 200, 240]}} # rhythmic flow
  - **Vertical Cascade**: emphasis on vertical movement
    {{x: [400, 380, 420, 360, 440], y: [80, 180, 280, 380, 460]}} # vertical emphasis
  - **Expanding Form**: growth from center outward
    {{x: [400, 350, 300, 450, 500, 320, 480], y: [250, 220, 200, 230, 260, 280, 290]}} # expanding
  - **Intersecting Paths**: crossing directional flows
    {{x: [150, 300, 450, 350, 200, 400], y: [200, 250, 300, 180, 160, 220]}} # intersecting

BRUSH TYPES AND CHARACTERISTICS:
Precision Tools:
pen: Clean, precise pen lines with consistent flow. Ideal for fine details, outlines, and technical drawing elements. Draws in black (no color selection).
marker: Broad marker strokes with semi-transparent blending. Good for filling areas and creating bold, graphic elements. **CUSTOMIZABLE COLOR** - choose from the palette below.
Creative/Artistic Brushes:
crayon: Crayon-like strokes with textured effects. Creates natural crayon-like appearance with consistent, textured strokes. **CUSTOMIZABLE COLOR** - choose from the palette below.
wiggle: Playful wiggling lines with dynamic curves and organic movement. Adds whimsical, wavy character to strokes. **CUSTOMIZABLE COLOR** - choose from the palette below.
spray: Spray paint effect with particle dispersion and texture. Creates scattered, airy effects similar to aerosol painting. It creates very textured black dots (no color selection).
fountain: Fountain pen with diagonal slanted lines and smooth ink flow. Produces elegant, calligraphic-style strokes. Draws in black (no color selection).

{color_palette_info}

## CRITICAL: OUTPUT FORMAT REQUIREMENTS
**YOU MUST OUTPUT ONLY THE JSON OBJECT BELOW. NO OTHER TEXT, NO MARKDOWN, NO EXPLANATIONS, NO ADDITIONAL CONTENT.**

{{
  "brush": "string",
  "color": "string",
  "strokes": [
    {{
      "x": [number, number, number],
      "y": [number, number, number],
      "t": [number, number],
      "description": "string"
    }}
  ],
  "reasoning": "string"
}}

HOW IT WORKS:
brush: Pick one brush from the list above - VARY your selection!
color: Hex color code from the palette above for marker/crayon/wiggle, or "default" for pen/spray/fountain
x: List of 5-10 x positions (0 to 850) - plan these carefully for abstract curves!
y: List of 5-10 y positions (0 to 500) - same number as x, increase y to go DOWN!
t: Speed numbers (1-5) - one less than x/y numbers
description: What abstract element you're creating
reasoning: Why this approach creates pure abstract expression

SPEED CONTROL (the "t" numbers):
1 = Draw fast and straight
2-3 = Draw at normal speed
4-5 = Draw slow and smooth

Use slow speeds (4-5) for smooth organic curves and flowing abstract forms
Use fast speeds (1-2) for sharp geometric lines and structured abstract elements

**ABSTRACT COLOR GUIDELINES:**
- Choose colors ONLY from the palette above for marker/crayon/wiggle brushes
- Use color to create visual hierarchy and abstract composition
- Consider color relationships and contrast for pure abstract expression
- Let color guide the emotional quality of your abstract forms

Remember: Create pure abstract art that transcends representation! Let your imagination flow freely with shapes, lines, and colors from the palette!"""

    def _validate_and_sanitize_emotion(self, data: Dict, emotion: str) -> Dict:
        """Validate and sanitize the emotion drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["pen", "marker", "crayon", "wiggle", "spray", "fountain"]
        color_customizable_brushes = ["marker", "crayon", "wiggle"]

        # Ensure required fields exist
        brush = data.get("brush", "pen")
        if brush not in valid_brushes:
            brush = "pen"

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
                    "t": [2],
                    "description": f"default stroke for {emotion} mood"
                }
            ]

        # Validate strokes (same as regular validation)
        validated_strokes = []
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                x_coords = stroke["x"] if isinstance(stroke["x"], list) else [stroke["x"]]
                y_coords = stroke["y"] if isinstance(stroke["y"], list) else [stroke["y"]]
                timing = stroke.get("t", [])

                # Ensure same length for x and y
                min_len = min(len(x_coords), len(y_coords))
                x_coords = x_coords[:min_len]
                y_coords = y_coords[:min_len]

                # Validate timing array
                if not isinstance(timing, list):
                    timing = []

                # Timing should have length = len(x_coords) - 1
                expected_timing_len = max(0, len(x_coords) - 1)
                if len(timing) != expected_timing_len:
                    # Fill with default timing values
                    timing = [2] * expected_timing_len  # Default medium speed

                # Clamp timing values to 1-5
                timing = [max(1, min(5, int(t))) for t in timing]

                # Clamp coordinates to canvas bounds
                x_coords = [max(0, min(850, float(x))) for x in x_coords]
                y_coords = [max(0, min(500, float(y))) for y in y_coords]

                validated_strokes.append({
                    "x": x_coords,
                    "y": y_coords,
                    "original_x": x_coords,  # Keep original for reference
                    "original_y": y_coords,
                    "timing": timing,
                    "description": stroke.get("description", f"stroke for {emotion} mood")
                })

        return {
            "brush": brush,
            "color": color,
            "mood": data["mood"],
            "strokes": validated_strokes,
            "reasoning": data.get("reasoning", f"Expressing mood: {emotion}")
        }

    def _validate_and_sanitize_abstract(self, data: Dict) -> Dict:
        """Validate and sanitize the abstract drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["pen", "marker", "crayon", "wiggle", "spray", "fountain"]
        color_customizable_brushes = ["marker", "crayon", "wiggle"]

        # Ensure required fields exist
        brush = data.get("brush", "pen")
        if brush not in valid_brushes:
            brush = "pen"

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
                    "t": [3, 2],
                    "description": "default abstract stroke"
                }
            ]

        # Validate strokes (same as regular validation)
        validated_strokes = []
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                x_coords = stroke["x"] if isinstance(stroke["x"], list) else [stroke["x"]]
                y_coords = stroke["y"] if isinstance(stroke["y"], list) else [stroke["y"]]
                timing = stroke.get("t", [])

                # Ensure same length for x and y
                min_len = min(len(x_coords), len(y_coords))
                x_coords = x_coords[:min_len]
                y_coords = y_coords[:min_len]

                # Validate timing array
                if not isinstance(timing, list):
                    timing = []

                # Timing should have length = len(x_coords) - 1
                expected_timing_len = max(0, len(x_coords) - 1)
                if len(timing) != expected_timing_len:
                    # Fill with default timing values
                    timing = [2] * expected_timing_len  # Default medium speed

                # Clamp timing values to 1-5
                timing = [max(1, min(5, int(t))) for t in timing]

                # Clamp coordinates to canvas bounds
                x_coords = [max(0, min(850, float(x))) for x in x_coords]
                y_coords = [max(0, min(500, float(y))) for y in y_coords]

                # Ensure at least 2 points for a stroke
                if len(x_coords) >= 2:
                    # Interpolate stroke based on timing
                    interpolated_x, interpolated_y = self._interpolate_stroke_with_timing(
                        x_coords, y_coords, timing
                    )

                    validated_strokes.append({
                        "x": interpolated_x,
                        "y": interpolated_y,
                        "original_x": x_coords,  # Keep original for reference
                        "original_y": y_coords,
                        "timing": timing,
                        "description": stroke.get("description", "abstract stroke")
                    })

        if not validated_strokes:
            validated_strokes = [
                {
                    "x": [400, 425, 450],  # Interpolated version
                    "y": [250, 262, 275],
                    "original_x": [400, 450],
                    "original_y": [250, 275],
                    "timing": [2],
                    "description": "fallback abstract stroke"
                }
            ]

        reasoning = data.get("reasoning", "Abstract creative expression")[:300]

        return {
            "brush": brush,
            "color": color,
            "strokes": validated_strokes,
            "reasoning": reasoning
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

    def _interpolate_stroke_with_timing(self, x_coords: List[float], y_coords: List[float],
                                      timing: List[int]) -> tuple[List[float], List[float]]:
        """
        Interpolate stroke points using smooth curves instead of linear interpolation.

        Args:
            x_coords: Original x coordinates
            y_coords: Original y coordinates
            timing: Timing values between consecutive points

        Returns:
            Tuple of (interpolated_x, interpolated_y) with smooth curves
        """
        if len(x_coords) != len(y_coords):
            return x_coords, y_coords

        if len(timing) != len(x_coords) - 1:
            # If timing doesn't match, use default timing of 2 for all segments
            timing = [2] * (len(x_coords) - 1)

        # For smooth curves, we need at least 2 points
        if len(x_coords) < 2:
            return x_coords, y_coords

        interpolated_x = []
        interpolated_y = []

        # Helper function for Catmull-Rom spline interpolation
        def catmull_rom_point(p0, p1, p2, p3, t):
            """Calculate point on Catmull-Rom spline"""
            t2 = t * t
            t3 = t2 * t

            return 0.5 * ((2 * p1) +
                         (-p0 + p2) * t +
                         (2*p0 - 5*p1 + 4*p2 - p3) * t2 +
                         (-p0 + 3*p1 - 3*p2 + p3) * t3)

        # For each segment, create smooth curve interpolation
        for i in range(len(x_coords) - 1):
            # Get control points for Catmull-Rom spline
            # We need 4 points: p0, p1 (current segment start), p2 (current segment end), p3

            # Handle edge cases for first and last segments
            if i == 0:
                # First segment: extrapolate p0
                p0_x = x_coords[0] - (x_coords[1] - x_coords[0])
                p0_y = y_coords[0] - (y_coords[1] - y_coords[0])
            else:
                p0_x = x_coords[i - 1]
                p0_y = y_coords[i - 1]

            p1_x, p1_y = x_coords[i], y_coords[i]
            p2_x, p2_y = x_coords[i + 1], y_coords[i + 1]

            if i == len(x_coords) - 2:
                # Last segment: extrapolate p3
                p3_x = x_coords[-1] + (x_coords[-1] - x_coords[-2])
                p3_y = y_coords[-1] + (y_coords[-1] - y_coords[-2])
            else:
                p3_x = x_coords[i + 2]
                p3_y = y_coords[i + 2]

            # Number of interpolation steps based on timing
            steps = max(2, min(8, timing[i] * 2))  # More steps for smoother curves

            # Generate curve points
            for step in range(steps):
                t = step / (steps - 1)  # 0 to 1

                curve_x = catmull_rom_point(p0_x, p1_x, p2_x, p3_x, t)
                curve_y = catmull_rom_point(p0_y, p1_y, p2_y, p3_y, t)

                interpolated_x.append(curve_x)
                interpolated_y.append(curve_y)

        # Remove duplicate points (the last point of each segment = first point of next)
        if len(interpolated_x) > 1:
            final_x = [interpolated_x[0]]
            final_y = [interpolated_y[0]]

            for i in range(1, len(interpolated_x)):
                # Only add point if it's sufficiently different from the last one
                if abs(interpolated_x[i] - final_x[-1]) > 1 or abs(interpolated_y[i] - final_y[-1]) > 1:
                    final_x.append(interpolated_x[i])
                    final_y.append(interpolated_y[i])

            return final_x, final_y

        return interpolated_x, interpolated_y

    def _validate_and_sanitize(self, data: Dict) -> Dict:
        """Validate and sanitize the drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["pen", "marker", "crayon", "wiggle", "spray", "fountain"]
        color_customizable_brushes = ["marker", "crayon", "wiggle"]

        # Ensure required fields exist
        brush = data.get("brush", "pen")
        if brush not in valid_brushes:
            brush = "pen"

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
                    "t": [2],
                    "description": "default stroke"
                }
            ]

        # Validate strokes
        validated_strokes = []
        for stroke in strokes:
            if "x" in stroke and "y" in stroke:
                x_coords = stroke["x"] if isinstance(stroke["x"], list) else [stroke["x"]]
                y_coords = stroke["y"] if isinstance(stroke["y"], list) else [stroke["y"]]
                timing = stroke.get("t", [])

                # Ensure same length for x and y
                min_len = min(len(x_coords), len(y_coords))
                x_coords = x_coords[:min_len]
                y_coords = y_coords[:min_len]

                # Validate timing array
                if not isinstance(timing, list):
                    timing = []

                # Timing should have length = len(x_coords) - 1
                expected_timing_len = max(0, len(x_coords) - 1)
                if len(timing) != expected_timing_len:
                    # Fill with default timing values
                    timing = [2] * expected_timing_len  # Default medium speed

                # Clamp timing values to 1-5
                timing = [max(1, min(5, int(t))) for t in timing]

                # Clamp coordinates to canvas bounds
                x_coords = [max(0, min(850, x)) for x in x_coords]
                y_coords = [max(0, min(500, y)) for y in y_coords]

                # Ensure at least 2 points for a stroke
                if len(x_coords) >= 2:
                    # Interpolate stroke based on timing
                    interpolated_x, interpolated_y = self._interpolate_stroke_with_timing(
                        x_coords, y_coords, timing
                    )

                    validated_strokes.append({
                        "x": interpolated_x,
                        "y": interpolated_y,
                        "original_x": x_coords,  # Keep original for reference
                        "original_y": y_coords,
                        "timing": timing,
                        "description": stroke.get("description", "stroke")
                    })

        if not validated_strokes:
            validated_strokes = [
                {
                    "x": [400, 425, 450],  # Interpolated version
                    "y": [250, 262, 275],
                    "original_x": [400, 450],
                    "original_y": [250, 275],
                    "timing": [2],
                    "description": "fallback stroke"
                }
            ]

        reasoning = data.get("reasoning", "Creative expression")[:300]

        return {
            "brush": brush,
            "color": color,
            "strokes": validated_strokes,
            "reasoning": reasoning
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
                "description": stroke.get("description", "stroke"),
                "reasoning": instruction.reasoning,
                "x_coords": stroke.get("original_x", stroke.get("x", [])),
                "y_coords": stroke.get("original_y", stroke.get("y", [])),
                "x_range": (min(stroke.get("original_x", stroke.get("x", [400]))),
                           max(stroke.get("original_x", stroke.get("x", [400])))),
                "y_range": (min(stroke.get("original_y", stroke.get("y", [250]))),
                           max(stroke.get("original_y", stroke.get("y", [250])))),
                "center_x": sum(stroke.get("original_x", stroke.get("x", [400]))) / len(stroke.get("original_x", stroke.get("x", [400]))),
                "center_y": sum(stroke.get("original_y", stroke.get("y", [250]))) / len(stroke.get("original_y", stroke.get("y", [250])))
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
        for i, stroke in enumerate(self.stroke_history[-5:], 1):  # Last 5 strokes
            # Determine region
            center_x, center_y = stroke["center_x"], stroke["center_y"]
            region = self._get_canvas_region(center_x, center_y)

            context += f"Stroke {len(self.stroke_history) - 5 + i}: {stroke['description']}\n"
            context += f"  Location: {region} (center: {int(center_x)}, {int(center_y)})\n"
            context += f"  X range: {int(stroke['x_range'][0])}-{int(stroke['x_range'][1])}, Y range: {int(stroke['y_range'][0])}-{int(stroke['y_range'][1])}\n"
            context += f"  Brush: {stroke['brush']}\n"
            context += f"  Purpose: {stroke['reasoning'][:80]}...\n\n"

        context += "💡 SPATIAL AWARENESS TIPS:\n"
        context += "- Consider the positions of existing strokes when planning new ones\n"
        context += "- Use coordinate ranges to position elements relative to existing artwork\n"
        context += "- Build on or complement existing elements for cohesive composition\n"
        context += "- Canvas size is 850px wide × 500px tall\n"

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
        available_brushes = ["pen", "marker", "crayon", "wiggle", "spray", "fountain"]
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
            "brush": instruction.brush,
            "color": instruction.color,
            "strokes": instruction.strokes,
            "reasoning": instruction.reasoning
        }, indent=2))
    else:
        print(f"Canvas image not found: {canvas_path}")

if __name__ == "__main__":
    main()
