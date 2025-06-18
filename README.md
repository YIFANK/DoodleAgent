# Doodle Agent

An AI system that autonomously creates paintings using realistic paint brush simulation.

## Features
- Autonomous brush stroke decision-making using LLMs with visual context
- Realistic paint simulation using DLI-Paint WebGL engine
- Multiple artistic moods and styles
- Real-time visual feedback to AI decision-making

## Setup

1. Copy your DLI-Paint directory:
   \`\`\`bash
   cp -r /path/to/your/dli-paint ./
   \`\`\`

2. Run setup:
   \`\`\`bash
   python setup.py
   \`\`\`

3. Configure API keys in \`.env\`

4. Run the system:
   \`\`\`bash
   python autonomous_painter.py
   \`\`\`

## Project Structure
- \`autonomous_painter.py\` - Main system
- \`dli-paint/\` - Paint simulation engine
- \`config/\` - Configuration files
- \`output/\` - Generated paintings
- \`logs/\` - System logs