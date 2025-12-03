# Doodle Agent: Exploring Freeform Visual Generation with Multimodal LLMs

[![Paper](https://img.shields.io/badge/Paper-OpenReview-blue)](https://openreview.net/pdf?id=oT8pxhfPzT)
[![Website](https://img.shields.io/badge/Website-Live-green)](https://yifank.github.io/doodle-agent/)

This repository contains the code for **Doodle Agent**, an AI-powered creative drawing system that explores how large multimodal language models engage in open-ended visual creation through natural doodling. The agent iteratively selects brushes, colors, and coordinates to create freeform drawings without explicit instructions.

**Paper**: *Doodle Agent: Exploring Freeform Visual Generation with Multimodal LLMs*
**Authors**: Dingning Cao, Yifan Kang, Antonio Torralba, Yael Vinker
**Venue**: ICCV 2025 Workshop on AI4VA

## 🎨 Overview

Doodle Agent consists of three main components:

1. **FreeDrawingAgent** ([free_drawing_agent.py](free_drawing_agent.py)) - The AI artist that analyzes canvas images and generates drawing instructions
2. **DrawingCanvasBridge** ([drawing_canvas_bridge.py](drawing_canvas_bridge.py)) - The interface that executes drawing instructions on the HTML canvas
3. **Demo Script** ([demo_free_canvas.py](demo_free_canvas.py)) - Example usage and interactive demos

The system uses a web-based canvas built in p5.js with five brush types (marker, crayon, wiggle, spray, fountain) and a palette of 36 colors. At each step, the multimodal LLM (Claude 3.5 Sonnet or GPT-4o) receives the current canvas and outputs JSON commands specifying brush, color, and stroke coordinates.

## 🚀 Quick Start

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YIFANK/DoodleAgent.git
   cd DoodleAgent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Configuration**:
   Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```

3. **Chrome WebDriver**:
   Ensure you have Chrome browser installed and ChromeDriver in your PATH.

### Running the Demo

```bash
# Run the interactive demo
python demo_free_canvas.py

# Test just the agent (without browser)
python demo_free_canvas.py --test-agent
```

## 🎭 How It Works

### System Architecture

```
User Question + Canvas Image → FreeDrawingAgent → JSON Instructions → DrawingCanvasBridge → Canvas Updates
```

### Agent Workflow

1. **Canvas Analysis**: The agent receives the current canvas as an image
2. **Creative Decision**: Based on the canvas state and user question, it decides what to draw
3. **JSON Output**: Generates structured drawing instructions
4. **Execution**: The bridge translates JSON to actual drawing actions

### JSON Format

The agent outputs instructions in this exact format:

```json
{
  "brush": "pen",
  "color": "#ff0000",
  "strokes": [
    {
      "x": [100, 150, 200],
      "y": [100, 120, 100],
      "t": [2, 4],
      "description": "curved line"
    }
  ],
  "reasoning": "Adding a red curved line to complement the existing elements"
}
```

### 🕒 Timing Control Feature

The system now includes **stroke timing control** through the `t` field, which controls drawing speed and smoothness:

- **t[i]**: Controls interpolation between point `i` and point `i+1`
- **Values**: 1-5 (1=fast, 5=very slow with many intermediate points)
- **Length**: `t` array length = `x` array length - 1

#### Example:
```
Original: x=[10, 20, 30, 40], y=[10, 20, 30, 40], t=[1, 2, 5]
Result:   x=[10, 20, 25, 30, 32, 34, 36, 38, 40]
```

**Breakdown:**
- 10→20: t=1 (no interpolation, direct line)
- 20→30: t=2 (1 intermediate point: 25)  
- 30→40: t=5 (4 intermediate points: 32, 34, 36, 38)

#### When to Use Different Timing Values:

**t=1 (Fast)**: Structural lines, geometric shapes, quick pen strokes
**t=2-3 (Medium)**: General drawing, moderate curves
**t=4-5 (Slow)**: Artistic curves, rainbow/spray effects, smooth organic shapes

## 🖌️ Available Brushes

The agent can use any of these brushes from [wisteria.html](wisteria.html):

- **pen**: Clean, precise pen lines (2px width)
- **marker**: Broad semi-transparent marker strokes (50px diameter)
- **rainbow**: Animated rainbow colors that cycle through the spectrum
- **wiggle**: Playful wiggling lines with curves and organic movement
- **spray**: Spray paint effect with particle dispersion
- **fountain**: Fountain pen with diagonal slanted lines

## 📝 Usage Examples

### Basic Agent Usage

```python
from free_drawing_agent import FreeDrawingAgent
import os

# Initialize the agent
api_key = os.getenv("ANTHROPIC_API_KEY")
agent = FreeDrawingAgent(api_key=api_key)

# Generate drawing instruction
instruction = agent.create_drawing_instruction(
    canvas_image_path="my_canvas.png",
    user_question="What would you like to draw next?"
)

print(f"Agent wants to use {instruction.brush} brush")
print(f"Reasoning: {instruction.reasoning}")
```

### Full Automated Session

```python
from drawing_canvas_bridge import AutomatedDrawingCanvas
import os

# Initialize automated canvas
api_key = os.getenv("ANTHROPIC_API_KEY")
canvas = AutomatedDrawingCanvas(api_key=api_key)

# Start the interface
canvas.start()

# Run a creative session
canvas.creative_session(num_iterations=5)

# Clean up
canvas.close()
```

### Interactive Drawing

```python
# Single drawing step
instruction = canvas.draw_from_canvas(
    canvas_filename="current_canvas.png",
    question="Add something colorful to this scene"
)
```

## 🎨 Demo Modes

The demo script offers several interaction modes:

1. **Quick Demo**: 3 automated drawing steps
2. **Extended Demo**: 7 automated drawing steps  
3. **Custom Demo**: Specify your own number of steps
4. **Interactive Demo**: You ask questions, the AI responds with drawings

## 🔧 Customization

### Modifying the Agent

You can customize the agent's behavior by modifying the system prompt in `_get_system_prompt()`:

```python
def _get_system_prompt(self) -> str:
    return """Your custom artist personality and instructions here..."""
```

### Adding New Brushes

To support additional brushes:

1. Update the `valid_brushes` list in `_validate_and_sanitize()`
2. Add the brush mapping in `DrawingCanvasBridge.set_brush()`
3. Update the system prompt to describe the new brush

### Canvas Dimensions

The current canvas is 850×500 pixels. Coordinates are automatically clamped to these bounds.

## 📁 Project Structure

```
DoodleAgent/
├── free_drawing_agent.py       # Main agent implementation
├── drawing_canvas_bridge.py    # Canvas interface bridge
├── demo_free_canvas.py         # Demo script
├── wisteria.html               # Main drawing interface
├── requirements.txt            # Core dependencies
├── scripts/                    # Analysis and utility scripts
│   ├── analyze_mood.py
│   ├── unified_analysis.py
│   ├── run_comprehensive_analysis.py
│   ├── stroke_data_processor.py
│   ├── color_grouping.py
│   ├── log_viewer.py
│   ├── demo_video_generation_lite.py
│   └── explorer_demo.py
├── tests/                      # Test files
│   ├── brush_step_test.py
│   ├── wiggle_brush_shape_test.py
│   ├── simple_test.py
│   ├── test_custom_outputs.py
│   ├── test_drawing_bridge.py
│   └── test_human_outputs.py
├── examples/                   # Example files
│   ├── env_example.txt
│   ├── humandoodle_test_10.json
│   └── strokes.json
├── docs/                       # Additional documentation
│   ├── README_EmotionDrawing.md
│   ├── VIDEO_GENERATION_README.md
│   └── human_stroke_collector_README.md
└── utils/                      # Evaluation utilities
```

## 🐛 Troubleshooting

### Common Issues

1. **Canvas not found**: Ensure [wisteria.html](wisteria.html) is in the same directory
2. **ChromeDriver issues**: Make sure ChromeDriver is installed and in PATH
3. **API errors**: Verify your Anthropic API key is correct and has credits
4. **Stroke execution fails**: Check that coordinates are within canvas bounds (0-850, 0-500)

## 📊 Analysis Scripts

The [scripts/](scripts/) directory contains tools for analyzing drawing data:

- **analyze_mood.py**: Analyze color usage across different moods
- **unified_analysis.py**: Evaluate JSON files from both custom and human datasets
- **run_comprehensive_analysis.py**: Run comprehensive analysis for all datasets
- **stroke_data_processor.py**: Process stroke data from the canvas interface

Run analysis scripts from the project root:
```bash
python scripts/unified_analysis.py --dataset all
python scripts/analyze_mood.py
```

### Debug Mode

Enable verbose logging by adding debug prints in the bridge:

```python
# In drawing_canvas_bridge.py
def execute_stroke(self, stroke: dict):
    print(f"DEBUG: Executing stroke: {stroke}")
    # ... rest of method
```

## 📊 Output Files

The system saves various files in the `output/` directory:

- `canvas_initial.png`: Starting blank canvas
- `canvas_step_N.png`: Canvas after each drawing step
- `final_artwork.png`: Final completed artwork
- `interactive_final.png`: Final artwork from interactive sessions

## 🎯 Use Cases

This system is perfect for:

- **Creative AI Research**: Studying AI creativity and artistic decision-making
- **Art Therapy Applications**: Collaborative human-AI art creation
- **Educational Demos**: Teaching AI capabilities in creative domains
- **Prototype Development**: Building more sophisticated drawing AI systems
- **Entertainment**: Fun interactive art creation experiences

## 🔮 Future Enhancements

Potential improvements could include:

- **Style Transfer**: Teaching the agent specific artistic styles
- **Color Palette Learning**: Having the agent learn color harmony rules
- **Composition Analysis**: More sophisticated understanding of visual composition
- **Multi-Agent Collaboration**: Multiple AI artists working together
- **Real-time Interaction**: Streaming drawing updates as the agent works

## 📚 API Reference

### FreeDrawingAgent

```python
agent = FreeDrawingAgent(api_key, model="claude-3-5-sonnet-20241022")
instruction = agent.create_drawing_instruction(canvas_image_path, user_question)
```

### DrawingCanvasBridge

```python
bridge = DrawingCanvasBridge(canvas_url)
bridge.start_canvas_interface()
bridge.execute_instruction(instruction)
bridge.capture_canvas(filename)
bridge.close()
```

### AutomatedDrawingCanvas

```python
canvas = AutomatedDrawingCanvas(api_key, canvas_url)
canvas.start()
canvas.creative_session(num_iterations)
canvas.close()
```

## 📖 Citation

If you use this code in your research, please cite our paper:

```bibtex
@inproceedings{cao2025doodleagent,
  title     = {Doodle Agent: Exploring Freeform Visual Generation with Multimodal LLMs},
  author    = {Cao, Dingning and Kang, Yifan and Torralba, Antonio and Vinker, Yael},
  booktitle = {Proceedings of the IEEE/CVF International Conference on Computer Vision Workshops (ICCVW)},
  year      = {2025},
  note      = {AI4VA Workshop},
}
```

## 🤝 Contributing

To contribute to this project:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

Make sure to follow the existing code style and add appropriate documentation.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Website template based on [Nerfies](https://nerfies.github.io/)
- Drawing interface built with [p5.js](https://p5js.org/)
- Powered by [Anthropic Claude](https://www.anthropic.com/) and OpenAI GPT-4

---

**Happy Doodling! 🎨✨** 