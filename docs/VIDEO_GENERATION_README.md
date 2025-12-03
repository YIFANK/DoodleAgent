# 🎬 DoodleAgent Video Generation

This module allows you to generate MP4 videos from your drawing agent session logs, creating time-lapse videos of the creative drawing process.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_video.txt
```

### 2. Generate a Video

#### From the most recent session log:
```bash
python generate_drawing_video.py
```

#### From a specific log file:
```bash
python generate_drawing_video.py output/log/session_responses_20250622_181203.txt
```

#### With custom options:
```bash
python generate_drawing_video.py output/log/session_responses_20250622_181203.txt \
    --fps 12 \
    --duration 0.5 \
    --output my_custom_video.mp4
```

### 3. Run the Demo

```bash
python demo_video_generation.py
```

## 📁 Output

Videos are automatically saved to `output/video/` with names like:
- `drawing_session_20250622_181203.mp4`

## ⚙️ Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--fps` | 10 | Frames per second for the output video |
| `--duration` | 0.8 | Duration (seconds) to hold each step frame |
| `--output` | Auto | Custom output path for the video file |

## 🎨 Video Features

The generated videos include:

- **Step-by-step progression**: Shows each drawing instruction being executed
- **Text overlays**: Displays step numbers and agent reasoning
- **Mood tracking**: Shows the agent's emotional state for each step
- **Brush information**: Indicates which drawing tool was used
- **Smooth transitions**: Captures the gradual building of artwork

## 🔧 How It Works

1. **Parse Session Log**: Extracts drawing instructions from the log file
2. **Setup Canvas**: Launches the HTML drawing interface in a browser
3. **Replay Instructions**: Executes each drawing step in sequence
4. **Capture Frames**: Screenshots the canvas after each step
5. **Generate Video**: Combines frames into an MP4 using OpenCV

## 📋 Example Usage

```python
from generate_drawing_video import DrawingVideoGenerator

# Create generator with custom settings
generator = DrawingVideoGenerator(fps=15, frame_duration=0.5)

# Generate video from a log file
output_path = generator.generate_video(
    "output/log/session_responses_20250622_181203.txt"
)

print(f"Video saved to: {output_path}")
```

## 🛠️ Technical Details

### Dependencies
- **OpenCV**: For video encoding and image processing
- **Selenium**: For browser automation
- **NumPy**: For numerical operations
- **PIL**: For image handling

### Video Format
- **Codec**: MP4V (H.264 compatible)
- **Resolution**: 850x500 pixels (matching canvas size)
- **Quality**: High-quality frames with anti-aliasing

### Performance
- Processing time: ~2-5 seconds per drawing step
- File size: Typically 1-5 MB for 20-30 steps
- Memory usage: Moderate (temporary frame storage)

## 🎯 Tips for Best Results

1. **Use slower FPS** (8-12) for better viewing of artistic details
2. **Increase frame duration** (1.0+ seconds) for complex drawings
3. **Ensure stable browser** environment (close other tabs)
4. **Check log file quality** before generating videos

## 🐛 Troubleshooting

### Common Issues

**"No drawing instructions found"**
- Check that the log file contains valid JSON responses
- Ensure the log file format matches expected structure

**"Canvas not found"**
- Make sure Chrome/Chromium is installed
- Check that `drawing_canvas.html` exists
- Verify Selenium WebDriver is working

**"Video encoding failed"**
- Install OpenCV with video support: `pip install opencv-python`
- Check available disk space in output directory
- Ensure write permissions for output folder

### Debug Mode

For detailed logging, add debug prints:
```python
generator = DrawingVideoGenerator(fps=10, frame_duration=0.8)
generator.debug = True  # Enable verbose output
```

## 📈 Performance Optimization

- **Reduce FPS**: Lower values = faster processing
- **Shorter sessions**: Process logs with fewer steps
- **Cleanup temp files**: Script automatically cleans up
- **Browser headless mode**: Uncomment in bridge code for faster rendering

## 🎥 Video Examples

Generated videos showcase:
- Abstract art creation processes
- Emotional drawing progressions  
- Brush technique demonstrations
- Creative decision sequences

Perfect for:
- Understanding AI creativity
- Educational demonstrations
- Art process documentation
- Social media content

---

**Need help?** Check the main project README or create an issue with your specific use case! 