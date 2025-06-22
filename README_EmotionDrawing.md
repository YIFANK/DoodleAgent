# Autonomous Mood-Based Drawing Agent

This extension adds autonomous mood-driven art creation to the Free Drawing Agent. The AI autonomously determines artistic moods and creates artwork that captures different emotional atmospheres and artistic intentions without user input.

## Features

### 🎨 Autonomous Mood-Driven Art Creation
- **Autonomous Mood Selection**: The AI determines the artistic mood for each session
- **Intentional Stroke Planning**: Every mark serves the autonomously chosen mood
- **Mood-Specific Brushes**: Different brush types and styles for different moods
- **Speed Control**: Timing variations to match mood intensity
- **Cohesive Emotional Narrative**: All strokes belong to the same emotional world
- **No User Input Required**: The LLM makes all artistic decisions independently

### 🖌️ Mood-Adaptive Brushes
- **Energetic/Chaotic Moods**: Rainbow brush with fast speeds, bright colors, dynamic movements
- **Serene/Contemplative Moods**: Pen or fountain with slow speeds, smooth curves, gentle movements
- **Bold/Dramatic Moods**: Spray or marker with fast speeds, bold strokes, powerful patterns
- **Gentle/Delicate Moods**: Fountain or pen with slow speeds, soft curves, subtle movements
- **Mysterious/Whimsical Moods**: Wiggle with varying speeds, organic patterns, playful movements
- **Nostalgic/Dreamy Moods**: Rainbow or marker with medium speeds, flowing curves, warm colors

## Usage

### 1. Autonomous Mood-Based Demo
Run the interactive autonomous mood demo:
```bash
python demo_free_canvas.py
```
Then select option 5: "Mood-Based Demo"

### 2. Test Autonomous Mood Generation
Test autonomous mood generation:
```bash
# Test multiple autonomous moods
python test_emotion_drawing.py

# Test single autonomous mood
python test_emotion_drawing.py --single
```

### 3. Programmatic Usage
```python
from free_drawing_agent import FreeDrawingAgent

agent = FreeDrawingAgent(api_key="your-api-key")

# Create autonomous mood-based drawing instruction
instruction = agent.create_emotion_drawing_instruction(
    canvas_image_path="current_canvas.png"
    # No mood parameter - LLM determines mood autonomously
)

print(f"Brush: {instruction.brush}")
print(f"Reasoning: {instruction.reasoning}")
print(f"Strokes: {len(instruction.strokes)}")
```

## Autonomous Mood Examples

The AI can autonomously choose from a wide range of artistic moods including:

### Contemplative Moods
- **melancholic** - Reflective, thoughtful, wistful
- **contemplative** - Deep thinking, meditative, introspective
- **nostalgic** - Warm memories, sentimental, dreamy
- **meditative** - Calm, focused, peaceful

### Dynamic Moods
- **energetic** - Lively, active, vibrant
- **chaotic** - Unpredictable, wild, intense
- **dynamic** - Powerful, moving, forceful
- **vibrant** - Bright, colorful, lively

### Peaceful Moods
- **serene** - Calm, tranquil, peaceful
- **tranquil** - Quiet, still, harmonious
- **peaceful** - Gentle, soothing, restful
- **calm** - Steady, composed, balanced

### Expressive Moods
- **bold** - Confident, strong, assertive
- **dramatic** - Intense, theatrical, powerful
- **passionate** - Emotional, intense, fervent
- **expressive** - Emotional, communicative, vivid

### Subtle Moods
- **gentle** - Soft, tender, mild
- **delicate** - Fine, fragile, subtle
- **subtle** - Understated, refined, nuanced
- **dreamy** - Ethereal, soft, imaginative

### Powerful Moods
- **mysterious** - Enigmatic, puzzling, intriguing
- **powerful** - Strong, commanding, influential
- **forceful** - Strong, determined, compelling
- **intense** - Concentrated, focused, strong

### Playful Moods
- **whimsical** - Playful, fanciful, imaginative
- **joyful** - Happy, cheerful, delighted
- **lively** - Animated, spirited, energetic
- **somber** - Serious, grave, solemn

## JSON Output Format

The autonomous mood-based drawing uses an enhanced JSON format:

```json
{
  "mood": "melancholic",
  "brush": "fountain",
  "strokes": [
    {
      "x": [100, 150, 200],
      "y": [250, 200, 250],
      "t": [4, 5],
      "description": "slow downward curve reflecting melancholic mood"
    }
  ],
  "reasoning": "Using fountain brush with slow, deliberate strokes to capture the reflective and wistful nature of the melancholic mood"
}
```

### Key Features of Autonomous Mood-Based Output
- **autonomous mood selection**: The AI determines the mood without user input
- **mood-aware reasoning**: Explains how the drawing elements serve the chosen mood
- **mood-optimized brush selection**: Brushes chosen specifically for mood expression
- **mood-appropriate timing**: Speed variations that match mood intensity
- **intentional stroke planning**: Every mark serves the emotional atmosphere

## Technical Implementation

### New Methods Added

#### FreeDrawingAgent Class
- `create_emotion_drawing_instruction(canvas_image_path, emotion=None)` - Creates autonomous mood-based drawing instructions
- `_get_emotion_system_prompt()` - Returns mood-specific system prompt
- `_validate_and_sanitize_emotion(data, emotion)` - Validates mood-based responses

#### AutomatedDrawingCanvas Class
- `draw_from_emotion(canvas_filename, emotion=None)` - Executes autonomous mood-based drawing on canvas

### System Prompt Features

The autonomous mood system prompt includes:
- **Mood-Based Doodle Generator**: Focus on autonomous artistic mood selection
- **Intentional Stroke Planning**: Every mark serves the autonomously chosen mood
- **Brush-Mood Mapping**: Specific brush recommendations for each mood type
- **Speed-Mood Relationships**: Timing guidelines for mood expression
- **Cohesive Emotional Narrative**: All strokes belong to the same emotional world
- **Enhanced JSON Format**: Includes mood field and mood-aware reasoning

## Examples

### Autonomous Melancholic Mood Expression
```json
{
  "mood": "melancholic",
  "brush": "fountain",
  "strokes": [
    {
      "x": [300, 350, 400],
      "y": [200, 250, 300],
      "t": [4, 5],
      "description": "slow downward curve reflecting melancholic mood"
    }
  ],
  "reasoning": "Using fountain brush with slow, deliberate strokes to capture the reflective and wistful nature of the melancholic mood"
}
```

### Autonomous Energetic Mood Expression
```json
{
  "mood": "energetic",
  "brush": "rainbow",
  "strokes": [
    {
      "x": [200, 250, 300, 350],
      "y": [300, 250, 200, 250],
      "t": [1, 1, 2],
      "description": "dynamic upward spiral expressing energetic mood"
    }
  ],
  "reasoning": "Using rainbow brush with fast upward spiral motion to capture the lively and vibrant feeling of the energetic mood"
}
```

## Output Files

The autonomous mood-based drawing creates several output files:
- `output/autonomous_mood_test/` - Test results for autonomous mood generation
- `output/mood_step_X.png` - Canvas captures for each mood step
- `output/mood_final.png` - Final mood-based artwork
- `output/autonomous_mood_test/autonomous_mood_X.json` - Detailed instructions for each autonomous mood

## Requirements

- Same requirements as the main Free Drawing Agent
- Additional dependencies: None (uses existing infrastructure)

## Future Enhancements

- **Mood Consistency**: Maintain the same mood throughout a session
- **Mood Evolution**: Gradually transition between moods over multiple strokes
- **Mood Memory**: Remember and build upon previous mood expressions
- **Mood Feedback**: User feedback to improve mood expression accuracy
- **Mood Categories**: Group moods by artistic style or emotional family
- **Mood Intensity**: Scale moods from subtle to intense autonomously
