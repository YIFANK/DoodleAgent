# Drawing Agent System

An LLM-powered drawing agent that uses Claude-3.5-Haiku to analyze text prompts and canvas images, then generates specific drawing actions for a sophisticated digital painting interface.

## Overview

This system combines:
- **Advanced Painting Interface** (`painter.html`) - A sophisticated HTML5 canvas with multiple brush types and effects
- **LLM Drawing Agent** (`drawing_agent.py`) - Claude-powered agent that analyzes prompts and generates drawing actions
- **Automation Bridge** (`painting_bridge.py`) - Selenium-based automation to execute drawing actions
- **Demo Script** (`demo.py`) - Example usage and demonstrations

## Features

### Painting Interface
- **4 Brush Types**: Flowing Particle, Watercolor, Crayon, Oil Paint
- **Real-time Effects**: Particle systems, bleeding, texture simulation
- **Save Functionality**: Export artwork as PNG files
- **Natural Drawing**: Free-form mouse-based drawing with brush effects

### Drawing Agent
- **Text-to-Art**: Converts natural language descriptions into drawing actions
- **Canvas Analysis**: Understands current canvas state and builds upon it
- **Sequential Drawing**: Processes multiple prompts to build complex artwork
- **Intelligent Brush Selection**: Chooses appropriate brushes for different tasks
- **Natural Mouse Actions**: Uses mousedown, mousemove, mouseup for free-form drawing

## Installation

1. **Clone or download the project files**

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chrome WebDriver**:
   - Download ChromeDriver from: https://chromedriver.chromium.org/
   - Make sure it's in your PATH or specify the path in the code

4. **Set up Anthropic API key**:
   - Copy `env_example.txt` to `.env`
   - Edit `.env` and replace `your-api-key-here` with your actual Anthropic API key
   - Get your API key from: https://console.anthropic.com/

## Usage

### Quick Demo
Run the demo script to see the system in action:
```bash
python demo.py
```

This will create three different artworks:
- A landscape scene
- Abstract art
- A portrait sketch

### Custom Usage

```python
from painting_bridge import AutomatedPainter
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize the painter
painter = AutomatedPainter(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    painter_url="file:///path/to/painter.html"
)

# Start the interface
painter.start()

# Create artwork from prompts
prompts = [
    "Draw a sunset over mountains",
    "Add a flowing river in the foreground",
    "Include some trees along the riverbank"
]

actions = painter.paint_sequence(prompts)

# Save the result
painter.bridge.capture_canvas("my_artwork.png")

# Clean up
painter.close()
```

### Manual Painting Interface
You can also use the painting interface directly by opening `painter.html` in a web browser.

## System Architecture

### 1. Agent Prompt (`agent_prompt.md`)
- Comprehensive prompt that teaches Claude how to analyze prompts and canvas images
- Defines available brushes and their characteristics
- Specifies output format for drawing actions with mouse movements
- Provides guidelines for natural drawing techniques

### 2. Drawing Agent (`drawing_agent.py`)
- `DrawingAgent` class that interfaces with Claude API
- Analyzes text prompts and canvas images
- Generates structured drawing actions with mouse movements
- Handles API communication and error recovery

### 3. Painting Bridge (`painting_bridge.py`)
- `PaintingBridge` class for browser automation
- `AutomatedPainter` class for high-level orchestration
- Executes mouse-based drawing actions on the HTML canvas
- Captures canvas state for feedback loops

### 4. Painting Interface (`painter.html`)
- Sophisticated HTML5 canvas with multiple brush types
- Real-time particle systems and effects
- Natural drawing with mouse input
- Save functionality for artwork export

## Brush Types and Characteristics

### Flowing Particle Brush
- **Best for**: Abstract art, flowing lines, dynamic effects, hair, water, smoke
- **Characteristics**: Dynamic particle system with flowing effects
- **Drawing Style**: Use flowing, continuous movements

### Watercolor Brush
- **Best for**: Soft, organic shapes, color blending, natural media effects, skies, backgrounds
- **Characteristics**: Realistic watercolor with bleeding effects
- **Drawing Style**: Use gentle, overlapping strokes

### Crayon Brush
- **Best for**: Sketchy lines, textured surfaces, rough drawings, outlines, sketches
- **Characteristics**: Textured waxy application with natural gaps
- **Drawing Style**: Use short, textured strokes

### Oil Paint Brush
- **Best for**: Bold strokes, thick paint effects, traditional painting styles, details, highlights
- **Characteristics**: Thick impasto application with paint depletion
- **Drawing Style**: Use bold, confident strokes

## Output Format

The agent outputs JSON actions in this format:
```json
{
  "action": "draw",
  "brush": "watercolor",
  "color": "#ff6b6b",
  "strokes": [
    {
      "type": "stroke",
      "points": [
        {"x": 100, "y": 100, "action": "mousedown"},
        {"x": 150, "y": 120, "action": "mousemove"},
        {"x": 200, "y": 140, "action": "mousemove"},
        {"x": 250, "y": 150, "action": "mouseup"}
      ],
      "description": "Draw a flowing line"
    }
  ],
  "reasoning": "Using watercolor for organic shapes"
}
```

## Mouse Action Types

- **mousedown**: Start a new stroke
- **mousemove**: Continue the stroke with movement
- **mouseup**: End the stroke

## Drawing Techniques

### Natural Drawing:
- **Free-form strokes**: Use multiple points to create natural curves
- **Pressure simulation**: Vary stroke length and speed
- **Layering**: Build up effects with multiple strokes
- **Brush switching**: Change brushes mid-drawing for different effects

### Complex Shapes:
- **Circles**: Use multiple small strokes in circular patterns
- **Curves**: Use smooth, flowing mouse movements
- **Textures**: Use short, overlapping strokes
- **Gradients**: Use overlapping strokes with color variations

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**:
   - Download ChromeDriver and add to PATH
   - Or specify the path in the code

2. **API key errors**:
   - Make sure ANTHROPIC_API_KEY is set correctly
   - Check that your API key has sufficient credits

3. **Canvas not loading**:
   - Ensure painter.html is accessible
   - Check file paths in the code

4. **Drawing actions not executing**:
   - Check browser console for JavaScript errors
   - Ensure canvas element is properly loaded

### Debug Mode
Add debug prints to see what's happening:
```python
painter.bridge.driver.execute_script("console.log('Debug info');")
```

## Extending the System

### Adding New Brush Types
1. Add brush configuration to `painter.html`
2. Update the agent prompt with new brush information
3. Add brush selection logic in `painting_bridge.py`

### Custom Drawing Actions
1. Define new stroke types in the agent prompt
2. Implement stroke execution in `execute_stroke()` method
3. Update the JSON output format as needed

### Integration with Other LLMs
1. Modify `drawing_agent.py` to use different API endpoints
2. Adjust the prompt format for the target LLM
3. Update response parsing logic

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to submit issues, feature requests, or pull requests to improve the system.