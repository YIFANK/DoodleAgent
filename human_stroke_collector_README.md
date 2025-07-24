# Human Stroke Collector

This implementation adds human stroke collection functionality to the drawing canvas, allowing you to capture drawing data in the same format expected by drawing agents.

## Features

- **Real-time stroke collection**: Captures x,y coordinates at a fixed 60fps rate while drawing
- **Multiple stroke support**: Each drawing gesture is recorded as a separate stroke
- **Agent-compatible format**: Exports data in the exact format used by `free_drawing_agent.py`
- **Visual feedback**: Shows stroke count in real-time
- **Easy export**: One-click JSON export with timestamps

## How It Works

### Data Collection
- Coordinates are captured every ~16ms (60fps) while the mouse is pressed and moving
- Each drawing gesture (mouse press to release) creates a new stroke
- Only strokes with multiple points are saved (filters out single clicks)
- Data is automatically rounded to integer pixel coordinates

### Data Format
The exported JSON follows this structure:
```json
{
  "strokes": [
    {
      "x": [400, 450, 500, 525, 550],
      "y": [250, 200, 275, 300, 320]
    },
    {
      "x": [100, 150, 200],
      "y": [150, 175, 200]
    }
  ]
}
```

This matches exactly the format expected by your drawing agents.

## Usage

### 1. Drawing and Collection
1. Open `drawing_canvas.html` in a web browser
2. Draw on the canvas using any brush tool
3. Watch the stroke counter in the bottom-right update in real-time
4. Continue drawing multiple strokes as needed

### 2. Exporting Data
- Click "💾 Export Strokes" to download a JSON file with your stroke data
- Files are automatically named with timestamps: `strokes_YYYYMMDD_HHMMSS.json`

### 3. Managing Strokes
- **Clear Strokes**: Removes only the collected stroke data (keeps the drawing)
- **Clear Canvas**: Removes both the drawing and stroke data
- The stroke counter shows how many strokes have been collected

### 4. Processing Data
Use the included `stroke_data_processor.py` script to:

```bash
# Install required packages
pip install matplotlib numpy

# Run the processor (automatically finds latest stroke file)
python stroke_data_processor.py
```

The processor will:
- Load and analyze your stroke data
- Show statistics (number of strokes, points, lengths)
- Create a visualization of all strokes
- Save data in agent-compatible format

## Technical Details

### Sampling Rate
- Fixed 60fps collection rate (16.67ms intervals)
- Ensures consistent temporal resolution regardless of drawing speed
- Matches the frame rate of the drawing canvas

### Coordinate System
- Origin (0,0) at top-left corner
- X increases rightward, Y increases downward
- Coordinates are canvas-relative (not screen-relative)
- Integer pixel precision

### Browser Compatibility
- Works in all modern browsers
- Uses standard HTML5 Canvas and JavaScript APIs
- No special plugins or extensions required

## Integration with Drawing Agents

The collected data can be directly used with your existing drawing agents:

```python
import json

# Load collected human strokes
with open('strokes_20250101_120000.json', 'r') as f:
    human_strokes = json.load(f)

# Use directly in your agent
agent_data = {
    "strokes": human_strokes["strokes"]
}
```

## File Structure

- `drawing_canvas.html` - Main drawing interface with stroke collection
- `stroke_data_processor.py` - Python utility for analyzing collected data
- `strokes_*.json` - Exported stroke data files (created when you export)

## Tips

1. **Smooth Drawing**: Draw at a moderate speed for best data quality
2. **Multiple Attempts**: Export data after each drawing session to avoid losing work
3. **Data Analysis**: Use the processor script to understand your drawing patterns
4. **Integration**: The collected data format is ready for direct use in ML training or analysis

The stroke collector maintains the same 60fps precision as your drawing agents, ensuring compatibility and consistency for training or comparison purposes. 