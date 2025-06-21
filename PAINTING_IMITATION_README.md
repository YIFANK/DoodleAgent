# Painting Imitation Demo

This demo tests the agent's ability to imitate an existing painting by analyzing an input image and drawing something as close as possible to it using the available drawing tools.

## Overview

The Painting Imitation Demo (`painting_imitation_demo.py`) allows you to:
- Provide any input image for the agent to imitate
- Watch the agent analyze the target image and plan its approach
- See the agent progressively refine its imitation through multiple stages
- The agent stops when it thinks it has reached a satisfactory level of imitation

## Features

- **Target Image Analysis**: The agent analyzes the composition, colors, shapes, and style of the input image
- **Progressive Refinement**: The agent builds up the imitation layer by layer, starting with basic elements
- **Self-Assessment**: The agent continuously compares its work with the target and decides when to stop
- **Multiple Output Formats**: Saves both the final result and intermediate stages for analysis
- **Configurable Parameters**: Adjustable maximum stages and output file naming
- **Organized Output**: All files are saved to organized subdirectories

## Usage

### Basic Usage
```bash
python painting_imitation_demo.py --input-image path/to/your/image.png
```

### Advanced Usage
```bash
python painting_imitation_demo.py \
    --input-image path/to/your/image.png \
    --output-prefix my_imitation \
    --max-stages 20 \
    --output-dir my_output_folder
```

### Command Line Arguments

- `--input-image, -i` (required): Path to the target image to imitate
- `--output-prefix, -o` (optional): Prefix for output files (default: "imitation")
- `--max-stages, -m` (optional): Maximum number of imitation stages (default: 15)
- `--output-dir, -d` (optional): Output directory for all files (default: "output")

### Example with Test Image

1. First, create a test image:
```bash
python create_test_image.py
```

2. Run the imitation demo:
```bash
python painting_imitation_demo.py --input-image output/test_images/test_imitation_target.png
```

## Output Organization

All output files are organized in the following structure:

```
output/
├── painting_imitation/          # Painting imitation demo files
│   ├── imitation_stage_0.png   # Initial blank canvas
│   ├── imitation_stage_1.png   # First drawing stage
│   ├── imitation_stage_2.png   # Second drawing stage
│   ├── ...
│   └── imitation_final_imitation.png  # Final result
├── free_explorer/              # Free explorer demo files
├── autonomous_explorer/        # Autonomous explorer demo files
├── creative_explorer/          # Creative explorer demo files
├── test_images/                # Test and demo images
└── misc/                       # Miscellaneous files
```

### Organizing Output Files

To organize existing output files into subdirectories:
```bash
python organize_output.py
```

## Output Files

The demo generates several files in the `output/painting_imitation/` directory:
- `{prefix}_stage_0.png`: Initial blank canvas
- `{prefix}_stage_1.png`, `{prefix}_stage_2.png`, etc.: Intermediate stages
- `{prefix}_final_imitation.png`: Final imitation result
- `{prefix}_target.png`: Temporary copy of the target image (deleted after completion)

## How It Works

1. **Initial Analysis**: The agent receives the target image and analyzes its visual elements
2. **Planning Phase**: The agent creates a strategy for recreating the image using available tools
3. **Progressive Building**: The agent starts with fundamental elements and builds up details
4. **Continuous Comparison**: At each stage, the agent compares its work with the target
5. **Self-Assessment**: The agent decides when it's satisfied with the imitation quality
6. **Completion**: The process stops when the agent indicates satisfaction or max stages is reached

## Agent Capabilities

The agent can use:
- **Multiple Brush Types**: flowing, watercolor, crayon, oil
- **Color Matching**: Hex color codes to match target colors
- **Multi-point Strokes**: Precise control over drawing paths
- **Layered Approach**: Building complex images from simple elements

## Tips for Best Results

1. **Choose Appropriate Images**: Simple geometric patterns, landscapes, or abstract art work well
2. **Consider Complexity**: Very detailed or photorealistic images may be challenging
3. **Monitor Progress**: Check intermediate stages to see the agent's approach
4. **Adjust Stages**: Increase max-stages for complex images, decrease for simple ones
5. **Use Organized Output**: All files are automatically organized in subdirectories

## Troubleshooting

- **API Key**: Ensure `ANTHROPIC_API_KEY` is set in your `.env` file
- **Image Format**: Use common formats like PNG, JPG, or JPEG
- **File Paths**: Use absolute paths or ensure relative paths are correct
- **Browser Issues**: The demo opens a browser window; ensure it's not blocked
- **Output Directory**: The demo automatically creates the output directory if it doesn't exist

## Comparison with Other Demos

- **Free Explorer Demo**: Agent has complete creative freedom
- **Painting Imitation Demo**: Agent follows a specific target image
- **Autonomous Explorer Demo**: Agent explores with some guidance

The imitation demo is particularly useful for testing the agent's:
- Visual analysis capabilities
- Color matching accuracy
- Spatial reasoning
- Self-assessment abilities
- Progressive refinement skills

## File Organization

The system automatically organizes all output files:

- **Demo-specific folders**: Each demo type has its own subdirectory
- **Test images**: All test and demo images are stored separately
- **Automatic cleanup**: Temporary files are automatically removed
- **Easy navigation**: Clear folder structure makes it easy to find specific files 