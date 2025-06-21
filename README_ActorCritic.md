# Actor-Critic Brush Explorer

This is an advanced AI agent system that explores digital painting brushes using an **Actor-Critic architecture** where both the Actor and Critic are powered by Large Language Models (LLMs).

## Architecture Overview

### 🎭 Actor Agent (Enhanced Drawing Agent)
The Actor is responsible for making creative decisions:
- **Brush Selection**: Chooses from 11 available brush types (watercolor, crayon, oil, pen, marker, rainbow, wiggle, spray, fountain, splatter, toothpick)
- **Color Choice**: Selects colors from a curated palette
- **Stroke Creation**: Decides where and how to draw
- **Parameter Adjustment**: Sets brush-specific parameters for optimal effects
- **Feedback Integration**: Incorporates critic feedback into future decisions

### 🔍 Critic Agent (Art Evaluation LLM)
The Critic provides objective artwork evaluation:
- **Scoring**: Rates artwork on a 0-10 scale
- **Strength Analysis**: Identifies what works well in the composition
- **Weakness Detection**: Points out areas needing improvement
- **Specific Suggestions**: Provides actionable feedback for the next steps
- **Progression Tracking**: Considers artistic development over time

## Key Features

### 1. **Iterative Improvement Loop**
```
Canvas State → Critic Evaluation → Actor Decision → Action Execution → New Canvas State
```

### 2. **Dynamic Artistic Goals**
- Abstract compositions with dynamic movement
- Color harmony and contrast exploration
- Brush texture experimentation
- Visual focal point development
- Depth creation through layering

### 3. **Comprehensive Brush Support**
All 11 brushes from `allbrush.html` with their unique characteristics:
- **Watercolor**: Realistic bleeding and organic flow
- **Crayon**: Textured waxy application with paper interaction
- **Oil**: Thick impasto with natural paint depletion
- **Pen**: Clean, precise lines
- **Marker**: Semi-transparent broad strokes
- **Rainbow**: Dynamic color-changing effects
- **Wiggle**: Playful curved lines
- **Spray**: Particle dispersion effects
- **Fountain**: Diagonal slanted pen strokes
- **Splatter**: Colorful spray patterns
- **Toothpick**: Directional elliptical brush

### 4. **Intelligent Decision Making**
- **Confidence Scoring**: Actor assesses confidence in decisions
- **Feedback Integration**: Uses critic input to improve choices
- **Goal Adaptation**: Changes artistic direction dynamically
- **History Awareness**: Learns from previous actions

## Usage

### Prerequisites
```bash
pip install anthropic selenium pillow python-dotenv
```

### Environment Setup
Create a `.env` file with your Anthropic API key:
```
ANTHROPIC_API_KEY=your-api-key-here
```

### Running the Explorer
```bash
cd DoodleAgent
python actor_critic_explorer.py
```

### Configuration Options
You can customize the exploration by modifying parameters in the `main()` function:

```python
explorer = ActorCriticExplorer(api_key)
explorer.explore_brushes(
    max_stages=30,  # Maximum exploration stages
    output_dir="output_actor_critic"  # Output directory
)
```

## Output Structure

The system generates several outputs:

### 1. **Canvas Progression**
- `stage_0_canvas.png` - Initial blank canvas
- `stage_1_canvas.png` - After first action
- `stage_N_canvas.png` - After each subsequent action

### 2. **Exploration Log** (`exploration_log.json`)
```json
{
  "total_stages": 25,
  "final_score": 8.2,
  "exploration_log": [
    {
      "stage": 1,
      "goal": "Create an abstract composition with dynamic movement",
      "actor_decision": {
        "brush": "flowing",
        "color": "#ff6b6b",
        "confidence": 0.75,
        "reasoning": "Starting with flowing particles to establish movement"
      },
      "critic_feedback": {
        "score": 6.5,
        "reasoning": "Good start with dynamic elements, needs more composition balance"
      }
    }
  ]
}
```

## How It Works

### 1. **Initialization**
- Loads the `allbrush.html` painting interface
- Initializes Actor and Critic LLM agents
- Sets up exploration parameters

### 2. **Exploration Loop**
For each stage:
1. **Critic Evaluation**: Analyzes current canvas state
2. **Feedback Processing**: Actor considers critic input
3. **Decision Making**: Actor chooses next action
4. **Execution**: Action is performed on canvas
5. **Logging**: Results are recorded

### 3. **Termination Conditions**
- Maximum stages reached
- Critic suggests artwork is complete (score ≥ 7.5)
- User interruption

### 4. **Final Assessment**
- Comprehensive final evaluation
- Complete exploration log export
- Performance metrics summary

## Advanced Features

### 1. **Contextual Memory**
- Tracks last 3 critic evaluations for consistency
- Maintains decision history for pattern recognition
- Considers artistic progression over time

### 2. **Dynamic Goal Setting**
- Changes artistic focus every 8 stages
- Prevents stagnation and encourages exploration
- Balances consistency with variety

### 3. **Confidence-Based Learning**
- Actor confidence adjusts based on critic scores
- Higher confidence with positive feedback
- Adaptive decision-making based on success patterns

### 4. **Error Recovery**
- Graceful handling of API failures
- Default fallback behaviors
- Robust error logging and recovery

## Comparison with Previous Approaches

| Feature | Free Explorer | Actor-Critic Explorer |
|---------|---------------|----------------------|
| Decision Making | Single LLM | Dual LLM (Actor + Critic) |
| Feedback Loop | None | Continuous evaluation |
| Learning | Limited | Iterative improvement |
| Artistic Growth | Random | Directed by criticism |
| Quality Assessment | Subjective | Objective scoring |
| Exploration Strategy | Free-form | Goal-directed |

## Technical Implementation

### 1. **LLM Integration**
- Uses Anthropic's Claude for both Actor and Critic
- Structured JSON responses for reliable parsing
- Context-aware prompting with feedback history

### 2. **Canvas Interaction**
- Selenium WebDriver for browser automation
- Real-time brush parameter adjustment
- Accurate stroke execution and canvas capture

### 3. **Data Management**
- Comprehensive logging of all decisions and feedback
- Progress tracking with detailed metadata
- Exportable results for analysis

## Future Enhancements

1. **Multi-Critic System**: Multiple specialized critics (composition, color, technique)
2. **Reinforcement Learning**: Integration with RL for policy optimization
3. **Style Transfer**: Learning from reference artworks
4. **Interactive Mode**: Human-in-the-loop feedback integration
5. **Brush Parameter Optimization**: Fine-tuning brush settings automatically

## Troubleshooting

### Common Issues
1. **WebDriver Setup**: Ensure ChromeDriver is installed and in PATH
2. **API Limits**: Monitor Anthropic API usage and rate limits
3. **Canvas Loading**: Verify `allbrush.html` path is correct
4. **Memory Usage**: Large exploration sessions may require system resources

### Debug Mode
Add debug logging by modifying the logging level:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## License

This project extends the original DoodleAgent codebase with actor-critic functionality for research and educational purposes. 