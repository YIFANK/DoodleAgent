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

        # Create logging directory if it doesn't exist
        if self.enable_logging:
            os.makedirs("output/log", exist_ok=True)

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
        """Log the complete agent interaction to a timestamped file"""
        if not self.enable_logging:
            return

        try:
            # Create timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            log_filename = f"output/log/agent_response_{timestamp}.json"

            # Prepare log data
            log_data = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "input": {
                    "canvas_image_path": canvas_image_path,
                    "user_question": user_question,
                    "canvas_image_exists": os.path.exists(canvas_image_path),
                    "canvas_image_size": os.path.getsize(canvas_image_path) if os.path.exists(canvas_image_path) else None
                },
                "raw_response": {
                    "content": raw_response,
                    "length": len(raw_response)
                },
                "parsing": {
                    "success": parsing_success,
                    "error_info": error_info
                },
                "parsed_instruction": {
                    "brush": parsed_instruction.brush,
                    "color": parsed_instruction.color,
                    "strokes": parsed_instruction.strokes,
                    "reasoning": parsed_instruction.reasoning,
                    "num_strokes": len(parsed_instruction.strokes)
                } if parsed_instruction else None
            }

            # Save log file
            with open(log_filename, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)

            print(f"📝 Agent interaction logged to: {log_filename}")

        except Exception as e:
            print(f"Warning: Failed to save log file: {e}")

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
                    "text": f"{user_question}\n\nLook at the current canvas and decide what you'd like to draw next. Output your drawing instruction in the required JSON format."
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
                max_tokens=5000,
                messages=[user_message],
                system=self._get_system_prompt()
            )

            # Extract the response content
            raw_response = response.content[0].text
            # Log the raw response if logging is enabled
            if self.enable_logging:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                log_file = f"output/log/response_{timestamp}.txt"
                try:
                    with open(log_file, "w") as f:
                        f.write(raw_response)
                except Exception as e:
                    print(f"Error saving response log: {e}")
            # Parse the JSON response
            action_data = self._parse_json_response(raw_response)

            # If parsing failed, create a default action
            if action_data is None:
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
                color="#000000",
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

        # Log the interaction
        self._log_agent_interaction(
            canvas_image_path, user_question, raw_response,
            parsed_instruction, parsing_success, error_info
        )

        return parsed_instruction

    def create_emotion_drawing_instruction(self, canvas_image_path: str, emotion: str = None) -> DrawingInstruction:
        """
        Create a mood-based drawing instruction that expresses a specific emotion.

        Args:
            canvas_image_path: Path to current canvas image
            emotion: Optional emotion to express (if None, LLM chooses autonomously)

        Returns:
            DrawingInstruction object with mood-based drawing instructions
        """

        # Encode the canvas image
        image_data = self.encode_image(canvas_image_path)

        # Prepare the user message
        if emotion:
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
                        "text": f"Express the mood '{emotion}' through your drawing. Look at the current canvas and create art that embodies this emotional atmosphere. Output your drawing instruction in the required JSON format."
                    }
                ]
            }
        else:
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
                        "text": "Look at the current canvas and choose an artistic mood that inspires you. Then create art that expresses that mood. Output your drawing instruction in the required JSON format."
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
                max_tokens=5000,
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
                action_data = {
                    "mood": emotion or "contemplative",
                    "brush": "pen",
                    "strokes": [
                        {
                            "x": [400, 450],
                            "y": [250, 275],
                            "t": [2],
                            "description": "default mood stroke"
                        }
                    ],
                    "reasoning": "Default action due to parsing failure"
                }
            else:
                parsing_success = True

            # Validate and sanitize the response
            validated_data = self._validate_and_sanitize_emotion(action_data, emotion)

            # Track brush usage for variety
            self._track_brush_usage(validated_data["brush"])

            # Create the drawing instruction
            parsed_instruction = DrawingInstruction(
                brush=validated_data["brush"],
                color="mood-based",  # Color is determined by brush type
                strokes=validated_data["strokes"],
                reasoning=f"Mood: {validated_data.get('mood', 'unknown')} - {validated_data.get('reasoning', 'No reasoning provided')}"
            )

        except Exception as e:
            parsing_success = False
            error_info = f"Exception during processing: {str(e)}"
            print(f"Error creating emotion drawing instruction: {e}")

            # Create a fallback instruction
            parsed_instruction = DrawingInstruction(
                brush="pen",
                color="mood-based",
                strokes=[
                    {
                        "x": [400, 450],
                        "y": [250, 275],
                        "t": [2],
                        "description": "fallback mood stroke"
                    }
                ],
                reasoning=f"Fallback instruction due to error: {str(e)}"
            )

        # Log the interaction
        self._log_agent_interaction(
            canvas_image_path=canvas_image_path,
            user_question=f"Emotion drawing: {emotion or 'autonomous mood selection'}",
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
                max_tokens=5000,
                messages=[user_message],
                system=self._get_abstract_system_prompt()
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
                action_data = {
                    "brush": "rainbow",
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
                color="abstract",  # Color is determined by brush type
                strokes=validated_data["strokes"],
                reasoning=f"Abstract creation: {validated_data.get('reasoning', 'No reasoning provided')}"
            )

        except Exception as e:
            parsing_success = False
            error_info = f"Exception during processing: {str(e)}"
            print(f"Error creating abstract drawing instruction: {e}")

            # Create a fallback instruction
            parsed_instruction = DrawingInstruction(
                brush="rainbow",
                color="abstract",
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
        return """You are a creative artist who loves to doodle! Draw whatever feels fun and interesting to you right now. Let your imagination run free.

Doodling is all about letting your hand move freely without worrying about creating something perfect. Here are some simple ways to get started:

**Start with basic shapes** - circles, squares, triangles, and lines. You can combine these into simple objects like houses, flowers, or faces. Don't worry about making them look realistic.

**Try repetitive patterns** - draw spirals, zigzags, or repeating geometric shapes. These are relaxing and help your hand get comfortable with the pen or pencil.

**Use whatever's handy** - the margins of notebooks, napkins, or scrap paper work perfectly. A basic pen or pencil is all you need.

**Let your mind wander** - doodle while on phone calls, during meetings, or when you're thinking. The goal isn't to create art, but to keep your hands busy while your brain processes other things.

**Build on what you draw** - if you draw a circle, maybe add a face inside it, or turn it into a sun with rays coming out. Let one shape inspire the next.

**Don't judge your doodles** - they're meant to be spontaneous and imperfect. Some of the best doodles come from just moving your pen around without any plan.

The beauty of doodling is that there are no rules. It's a form of visual thinking that can actually help with creativity and stress relief. Just start making marks on paper and see where they take you.


**You must output ONLY valid JSON in the EXACT structure shown below.**

## BRUSH TYPES AND CHARACTERISTICS:
### Precision Tools:
- **pen**: Clean, precise pen lines with consistent flow. Ideal for fine details, outlines, and technical drawing elements. Draws in black.
- **marker**: Broad marker strokes with semi-transparent blending. Good for filling areas and creating bold, graphic elements. Draws in orange with high transparency.
### Creative/Artistic Brushes:
- **rainbow**: Dynamic rainbow colors that change as you draw with flowing effects. Creates colorful, vibrant strokes that cycle through the spectrum. It draws in a gradient of rainbow colors consistently.
- **wiggle**: Playful wiggling lines with dynamic curves and organic movement. Adds whimsical, wavy character to strokes. Draws in orange.
- **spray**: Spray paint effect with particle dispersion and texture. Creates scattered, airy effects similar to aerosol painting. It creates very textured black dots.
- **fountain**: Fountain pen with diagonal slanted lines and smooth ink flow. Produces elegant, calligraphic-style strokes. Draws in black.

CANVAS SIZE: 850px wide × 500px tall

OUTPUT FORMAT:
{
  "brush": "string",
  "strokes": [
    {
      "x": [number, number, number],
      "y": [number, number, number],
      "t": [number, number],
      "description": "string"
    }
  ],
  "reasoning": "string"
}

HOW IT WORKS:
- brush: Pick one brush from the list above
- x: List of 3-8 x positions (0 to 850)
- y: List of 3-8 y positions (0 to 500) - same number as x
- t: Speed numbers (1-5) - one less than x/y numbers
- description: What you're drawing (keep it short)
- reasoning: Why you picked this (keep it simple)

SPEED CONTROL (the "t" numbers):
- 1 = Draw fast and straight
- 2-3 = Draw at normal speed
- 4-5 = Draw slow and smooth

Use slow speeds (4-5) when you want:
- Smooth curves
- Nice flowing lines
- Cool effects with rainbow/spray brushes

Use fast speeds (1-2) when you want:
- Quick straight lines
- Sharp edges
- Simple shapes

Just have fun and draw whatever comes to mind! Could be anything - animals, shapes, patterns, objects, abstract designs, or whatever makes you happy to create."""

    def _get_emotion_system_prompt(self) -> str:
        """Return the system prompt for mood-based drawing"""
        return """Mood-Based Doodle Generator
You are a creative artist who channels emotions through visual expression! You MUST ALWAYS start by choosing an artistic mood that will guide your entire composition, then plan each stroke to reflect and enhance that emotional atmosphere.

First, establish your mood. ALWAYS choose a single descriptive word that captures the emotional essence you want to express (e.g., melancholic, energetic, chaotic, serene, bold, gentle, nostalgic, mysterious, joyful, contemplative, etc.). This mood will be the foundation for every artistic decision you make. If the canvas is blank, choose a mood that inspires you to begin creating.

Plan each stroke with intention. Unlike free-form doodling, every mark you make should serve your chosen mood:

Consider how brush choice reinforces mood:
Creative brushes (rainbow, wiggle, spray) enhance moods
Speed settings should match emotional intensity
Build cohesive emotional narrative. Each stroke should feel like it belongs to the same emotional world. Let mood guide your composition choices:

**IMPORTANT: Vary your brush selection!** While maintaining mood consistency, experiment with different brushes to create visual interest and depth. Don't use the same brush for more than 2-3 consecutive strokes. Consider how different brushes can express different aspects of the same mood.

You must output ONLY valid JSON in the EXACT structure shown below.

BRUSH TYPES AND CHARACTERISTICS:
Precision Tools:
pen: Clean, precise pen lines with consistent flow. Ideal for fine details, outlines, and technical drawing elements. Draws in black.
marker: Broad marker strokes with semi-transparent blending. Good for filling areas and creating bold, graphic elements. Draws in orange with high transparency.
Creative/Artistic Brushes:
rainbow: Dynamic rainbow colors that change as you draw with flowing effects. Creates colorful, vibrant strokes that cycle through the spectrum. It draws in a gradient of rainbow colors consistently.
wiggle: Playful wiggling lines with dynamic curves and organic movement. Adds whimsical, wavy character to strokes. Draws in orange.
spray: Spray paint effect with particle dispersion and texture. Creates scattered, airy effects similar to aerosol painting. It creates very textured black dots.
fountain: Fountain pen with diagonal slanted lines and smooth ink flow. Produces elegant, calligraphic-style strokes. Draws in black.

CANVAS SIZE: 850px wide × 500px tall

OUTPUT FORMAT:
{
  "mood": "string",
  "brush": "string",
  "strokes": [
    {
      "x": [number, number, number],
      "y": [number, number, number],
      "t": [number, number],
      "description": "string"
    }
  ],
  "reasoning": "string"
}

HOW IT WORKS:
mood: Your chosen emotional atmosphere (single descriptive word) - ALWAYS include this!
brush: Pick one brush from the list above that best serves your mood - VARY your selection!
x: List of 3-8 x positions (0 to 850)
y: List of 3-8 y positions (0 to 500) - same number as x
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
- Use creative brushes (rainbow, wiggle, spray, fountain) for expression and emotion
- Consider how brush texture and color contribute to the mood

Remember: ALWAYS start with a mood! Vary your brush selection for visual interest! Every stroke should feel emotionally authentic to your chosen mood. Create art that makes others feel what you're expressing!"""

    def _get_abstract_system_prompt(self) -> str:
        """Return the system prompt for abstract drawing"""
        return """Abstract Doodle Generator
You are a visionary abstract artist who creates pure, non-representational art! Your mission is to create abstract doodles that exist beyond the physical world -  expressions of creativity, emotion, and imagination.

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

**IMPORTANT: Vary your brush selection!** Experiment with different brushes to create visual interest and depth. Don't use the same brush for more than 2-3 consecutive strokes. Each brush brings unique abstract qualities

You must output ONLY valid JSON in the EXACT structure shown below.

BRUSH TYPES AND CHARACTERISTICS:
Precision Tools:
pen: Clean, precise pen lines with consistent flow. Ideal for fine details, outlines, and technical drawing elements. Draws in black.
marker: Broad marker strokes with semi-transparent blending. Good for filling areas and creating bold, graphic elements. Draws in orange with high transparency.
Creative/Artistic Brushes:
rainbow: Dynamic rainbow colors that change as you draw with flowing effects. Creates colorful, vibrant strokes that cycle through the spectrum. It draws in a gradient of rainbow colors consistently.
wiggle: Playful wiggling lines with dynamic curves and organic movement. Adds whimsical, wavy character to strokes. Draws in orange.
spray: Spray paint effect with particle dispersion and texture. Creates scattered, airy effects similar to aerosol painting. It creates very textured black dots.
fountain: Fountain pen with diagonal slanted lines and smooth ink flow. Produces elegant, calligraphic-style strokes. Draws in black.

CANVAS SIZE: 850px wide × 500px tall

OUTPUT FORMAT:
{
  "brush": "string",
  "strokes": [
    {
      "x": [number, number, number],
      "y": [number, number, number],
      "t": [number, number],
      "description": "string"
    }
  ],
  "reasoning": "string"
}

HOW IT WORKS:
brush: Pick one brush from the list above - VARY your selection!
x: List of 3-8 x positions (0 to 850)
y: List of 3-8 y positions (0 to 500) - same number as x
t: Speed numbers (1-5) - one less than x/y numbers
description: What abstract element you're creating (e.g., "flowing organic curve", "geometric intersection", "pure color burst")
reasoning: Why this abstract approach creates the intended creative flow

SPEED CONTROL (the "t" numbers):
1 = Draw fast and straight
2-3 = Draw at normal speed
4-5 = Draw slow and smooth

Use slow speeds (4-5) for smooth curves and flowing lines
Use fast speeds (1-2) for sharp angles and dynamic energy

**BRUSH VARIETY GUIDELINES:**
- Don't use the same brush for more than 2-3 consecutive strokes
- Experiment with different brushes for different abstract qualities
- Use precision tools (pen, marker) for structure and definition
- Use creative brushes (rainbow, wiggle, spray, fountain) for expression and flow
- Consider how brush texture and color contribute to the abstract composition

Remember: NO concrete objects! NO recognizable things! Create pure abstract art that flows from your imagination! Vary your brush selection! Let creativity guide you to something truly out of this world!"""

    def _validate_and_sanitize_emotion(self, data: Dict, emotion: str) -> Dict:
        """Validate and sanitize the mood-based drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["pen", "marker", "rainbow", "wiggle", "spray", "fountain"]

        # Ensure required fields exist
        brush = data.get("brush", "pen")
        if brush not in valid_brushes:
            brush = "pen"

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
            "mood": data["mood"],
            "strokes": validated_strokes,
            "reasoning": data.get("reasoning", f"Expressing mood: {emotion}")
        }

    def _validate_and_sanitize_abstract(self, data: Dict) -> Dict:
        """Validate and sanitize the abstract drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["pen", "marker", "rainbow", "wiggle", "spray", "fountain"]

        # Ensure required fields exist
        brush = data.get("brush", "pen")
        if brush not in valid_brushes:
            brush = "pen"

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
                        "description": stroke.get("description", "abstract stroke")[:20]
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

        reasoning = data.get("reasoning", "Abstract creative expression")[:100]

        return {
            "brush": brush,
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
        Interpolate stroke points based on timing values.

        Args:
            x_coords: Original x coordinates
            y_coords: Original y coordinates
            timing: Timing values between consecutive points

        Returns:
            Tuple of (interpolated_x, interpolated_y)
        """
        if len(x_coords) != len(y_coords):
            return x_coords, y_coords

        if len(timing) != len(x_coords) - 1:
            # If timing doesn't match, use default timing of 1 for all segments
            timing = [1] * (len(x_coords) - 1)

        interpolated_x = [x_coords[0]]  # Start with first point
        interpolated_y = [y_coords[0]]

        for i in range(len(x_coords) - 1):
            # Get current segment
            x1, y1 = x_coords[i], y_coords[i]
            x2, y2 = x_coords[i + 1], y_coords[i + 1]
            t_divisions = max(1, min(5, timing[i]))  # Clamp to 1-5

            # Add intermediate points if t_divisions > 1
            if t_divisions > 1:
                for step in range(1, t_divisions):
                    alpha = step / t_divisions
                    interp_x = x1 + alpha * (x2 - x1)
                    interp_y = y1 + alpha * (y2 - y1)
                    interpolated_x.append(interp_x)
                    interpolated_y.append(interp_y)

            # Add the end point of this segment
            interpolated_x.append(x2)
            interpolated_y.append(y2)

        return interpolated_x, interpolated_y

    def _validate_and_sanitize(self, data: Dict) -> Dict:
        """Validate and sanitize the drawing instruction data"""
        # Valid brushes for drawing_canvas.html
        valid_brushes = ["pen", "marker", "rainbow", "wiggle", "spray", "fountain"]

        # Ensure required fields exist
        brush = data.get("brush", "pen")
        if brush not in valid_brushes:
            brush = "pen"

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
                        "description": stroke.get("description", "stroke")[:20]
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

        reasoning = data.get("reasoning", "Creative expression")[:100]

        return {
            "brush": brush,
            "strokes": validated_strokes,
            "reasoning": reasoning
        }

    def _track_brush_usage(self, brush: str):
        """Track brush usage for variety encouragement"""
        self.recent_brushes.append(brush)
        if len(self.recent_brushes) > self.max_brush_history:
            self.recent_brushes.pop(0)

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
        available_brushes = ["pen", "marker", "rainbow", "wiggle", "spray", "fountain"]
        unused_brushes = [b for b in available_brushes if b not in self.recent_brushes[-2:]]
        if unused_brushes:
            context += f"Try one of these unused brushes: {', '.join(unused_brushes[:2])}. "

        return context

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
