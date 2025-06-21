#!/usr/bin/env python3
"""
Actor-Critic Brush Explorer for the Drawing Agent system.
This implements an actor-critic architecture where both the actor and critic are LLMs.

The Actor:
- Decides what brush to use, where to draw, and what parameters to set
- Makes creative decisions based on current canvas state and critic feedback

The Critic:
- Evaluates the current artwork objectively
- Provides specific feedback on composition, technique, and artistic merit
- Suggests improvements for the next action
"""

import os
import sys
import json
import time
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
import anthropic
from painting_bridge import AutomatedPainter
from drawing_agent import DrawingAgent, DrawingAction

# Load environment variables
load_dotenv()

@dataclass
class CriticFeedback:
    """Represents feedback from the critic LLM"""
    overall_score: float  # 0-10 rating
    strengths: List[str]
    weaknesses: List[str]
    specific_suggestions: List[str]
    continue_drawing: bool
    reasoning: str

@dataclass
class ActorDecision:
    """Enhanced decision from the actor LLM"""
    action: DrawingAction
    confidence: float  # 0-1 confidence in decision
    artistic_intent: str
    expected_outcome: str

class CriticAgent:
    """
    LLM-powered critic that evaluates artwork and provides feedback
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.evaluation_history = []
    
    def evaluate_artwork(self, canvas_image_path: str, artistic_context: str = "", 
                        previous_feedback: List[CriticFeedback] = None) -> CriticFeedback:
        """
        Evaluate the current artwork and provide detailed feedback
        
        Args:
            canvas_image_path: Path to current canvas image
            artistic_context: Context about what the artist is trying to achieve
            previous_feedback: History of previous feedback for consistency
            
        Returns:
            CriticFeedback object with detailed evaluation
        """
        
        # Encode the canvas image
        with open(canvas_image_path, "rb") as image_file:
            import base64
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Build the critique prompt
        critique_prompt = self._build_critique_prompt(artistic_context, previous_feedback)
        
        user_message = {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": critique_prompt
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_data
                    }
                }
            ]
        }
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[user_message],
                system=[{"type": "text", "text": self._get_critic_system_prompt()}]
            )
            
            content = response.content[0].text
            feedback = self._parse_critic_response(content)
            self.evaluation_history.append(feedback)
            
            return feedback
            
        except Exception as e:
            print(f"Error in critic evaluation: {e}")
            # Return default feedback
            return CriticFeedback(
                overall_score=5.0,
                strengths=["Effort shown"],
                weaknesses=["Evaluation failed"],
                specific_suggestions=["Continue drawing"],
                continue_drawing=True,
                reasoning="Default feedback due to evaluation error"
            )
    
    def _build_critique_prompt(self, artistic_context: str, previous_feedback: List[CriticFeedback]) -> str:
        """Build the critique prompt based on context and history"""
        
        base_prompt = f"""As an art critic, evaluate this digital artwork. Consider:

ARTISTIC CONTEXT: {artistic_context if artistic_context else "Free-form digital exploration"}

Please provide your evaluation in the following JSON format:
{{
    "overall_score": <0-10 rating>,
    "strengths": [<list of positive aspects>],
    "weaknesses": [<list of areas for improvement>],
    "specific_suggestions": [<specific actionable suggestions>],
    "continue_drawing": <true/false whether to continue>,
    "reasoning": "<detailed explanation of your evaluation>"
}}

Focus on:
1. Composition and visual balance
2. Use of color and brushwork
3. Artistic technique and execution
4. Creative expression and originality
5. Overall aesthetic appeal

Be constructive but honest in your critique."""

        if previous_feedback and len(previous_feedback) > 0:
            recent_feedback = previous_feedback[-2:]  # Last 2 feedback items
            feedback_summary = "\n".join([f"Previous critique: {fb.reasoning}" for fb in recent_feedback])
            base_prompt += f"\n\nPREVIOUS FEEDBACK CONTEXT:\n{feedback_summary}\n\nConsider this progression in your evaluation."
        
        return base_prompt
    
    def _get_critic_system_prompt(self) -> str:
        """System prompt for the critic LLM"""
        return """You are an experienced art critic specializing in digital art and experimental techniques. 
        You have a deep understanding of artistic principles, color theory, composition, and various digital painting techniques.
        
        Your role is to provide constructive, detailed feedback that helps artists improve their work. 
        You should be encouraging while also being honest about areas that need improvement.
        
        When evaluating artwork, consider both technical execution and creative expression. 
        Look for evidence of artistic growth and experimentation.
        
        Always provide your response in valid JSON format as specified in the prompt."""
    
    def _parse_critic_response(self, content: str) -> CriticFeedback:
        """Parse the critic's JSON response"""
        try:
            # Find JSON in the response
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                data = json.loads(json_str)
                
                return CriticFeedback(
                    overall_score=float(data.get("overall_score", 5.0)),
                    strengths=data.get("strengths", []),
                    weaknesses=data.get("weaknesses", []),
                    specific_suggestions=data.get("specific_suggestions", []),
                    continue_drawing=bool(data.get("continue_drawing", True)),
                    reasoning=data.get("reasoning", "")
                )
        except Exception as e:
            print(f"Error parsing critic response: {e}")
        
        # Default feedback if parsing fails
        return CriticFeedback(
            overall_score=5.0,
            strengths=["Continued effort"],
            weaknesses=["Unable to evaluate properly"],
            specific_suggestions=["Keep experimenting"],
            continue_drawing=True,
            reasoning="Default feedback due to parsing error"
        )

class EnhancedActorAgent(DrawingAgent):
    """
    Enhanced actor agent that incorporates critic feedback
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-5-haiku-20241022"):
        super().__init__(api_key, model)
        self.decision_history = []
        self.available_brushes = [
            "watercolor", "crayon", "oil", "pen", "marker",
            "rainbow", "wiggle", "spray", "fountain", "splatter", "toothpick"
        ]
        self.color_palette = [
            "#4a90e2", "#d2691e", "#8b4513", "#000000",
            "#ff7700", "#ff7800", "#3cb446", "#9b59b6", "#e74c3c",
            "#f39c12", "#2ecc71", "#3498db", "#34495e"
        ]
    
    def decide_with_feedback(self, canvas_image_path: str, critic_feedback: CriticFeedback = None,
                           artistic_goal: str = "Create expressive artwork") -> ActorDecision:
        """
        Make an artistic decision incorporating critic feedback
        
        Args:
            canvas_image_path: Path to current canvas
            critic_feedback: Feedback from the critic
            artistic_goal: Overall artistic goal
            
        Returns:
            ActorDecision with enhanced decision-making
        """
        
        # Build the actor prompt with critic feedback
        actor_prompt = self._build_actor_prompt(artistic_goal, critic_feedback)
        
        # Get the drawing action
        action = self.analyze_and_plan(actor_prompt, canvas_image_path)
        
        # Enhance the action with decision metadata
        decision = ActorDecision(
            action=action,
            confidence=self._calculate_confidence(critic_feedback),
            artistic_intent=artistic_goal,
            expected_outcome=action.reasoning
        )
        
        self.decision_history.append(decision)
        return decision
    
    def _build_actor_prompt(self, artistic_goal: str, critic_feedback: CriticFeedback = None) -> str:
        """Build the enhanced actor prompt with critic feedback"""
        
        base_prompt = f"""You are a creative digital artist exploring various brush techniques. 

ARTISTIC GOAL: {artistic_goal}

AVAILABLE BRUSHES: {', '.join(self.available_brushes)}
AVAILABLE COLORS: {', '.join(self.color_palette)}

Your task is to create the next stroke or set of strokes that will enhance the artwork."""

        if critic_feedback:
            feedback_text = f"""
CRITIC FEEDBACK (Score: {critic_feedback.overall_score}/10):

STRENGTHS: {', '.join(critic_feedback.strengths)}
AREAS FOR IMPROVEMENT: {', '.join(critic_feedback.weaknesses)}
SPECIFIC SUGGESTIONS: {', '.join(critic_feedback.specific_suggestions)}

CRITIC'S REASONING: {critic_feedback.reasoning}

Please consider this feedback in your next artistic decision."""
            
            base_prompt += feedback_text
        
        base_prompt += """

Provide your response as a JSON object with the following structure:
{
    "brush": "<brush_type>",
    "color": "<hex_color>",
    "strokes": [{"x": [x1, x2, ...], "y": [y1, y2, ...]}],
    "reasoning": "<your artistic reasoning>"
}

Be creative, experimental, and responsive to the feedback provided."""

        return base_prompt
    
    def _calculate_confidence(self, critic_feedback: CriticFeedback = None) -> float:
        """Calculate confidence in the decision based on various factors"""
        base_confidence = 0.7
        
        if critic_feedback:
            # Higher confidence if critic score is good
            score_factor = critic_feedback.overall_score / 10.0
            feedback_factor = len(critic_feedback.strengths) / max(1, len(critic_feedback.weaknesses))
            base_confidence = (base_confidence + score_factor + feedback_factor) / 3.0
        
        return min(1.0, max(0.1, base_confidence))

class ActorCriticExplorer:
    """
    Main class that orchestrates the actor-critic exploration
    """
    
    def __init__(self, api_key: str, painter_url: str = None):
        self.api_key = api_key
        self.painter_url = painter_url or f"file://{os.path.dirname(os.path.abspath(__file__))}/allbrush.html"
        
        # Initialize agents
        self.actor = EnhancedActorAgent(api_key)
        self.critic = CriticAgent(api_key)
        self.painter = AutomatedPainter(api_key, self.painter_url)
        
        # Exploration state
        self.exploration_log = []
        self.current_stage = 0
        self.artistic_goals = [
            "Create an abstract composition with dynamic movement using watercolor and oil brushes",
            "Explore color harmony and contrast with marker and pen techniques",
            "Experiment with different brush textures and techniques",
            "Build a composition with strong visual focal points using spray and splatter",
            "Create depth and atmosphere through layering with crayon and oil paint"
        ]
    
    def explore_brushes(self, max_stages: int = 25, output_dir: str = "output_actor_critic"):
        """
        Main exploration loop with actor-critic feedback
        """
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            print("🎭 Starting Actor-Critic Brush Explorer")
            print("=" * 60)
            
            # Start the painting interface
            self.painter.start()
            
            # Capture initial blank canvas
            initial_canvas = os.path.join(output_dir, "stage_0_canvas.png")
            self.painter.bridge.capture_canvas(initial_canvas)
            
            # Set initial artistic goal
            current_goal = random.choice(self.artistic_goals)
            print(f"🎯 Initial Artistic Goal: {current_goal}")
            
            # Exploration loop
            for stage in range(1, max_stages + 1):
                self.current_stage = stage
                print(f"\n🎨 === Stage {stage} ===")
                
                # Get canvas from previous stage
                prev_canvas = os.path.join(output_dir, f"stage_{stage-1}_canvas.png")
                
                # Critic evaluates current state (skip for first stage)
                critic_feedback = None
                if stage > 1:
                    print("🔍 Critic evaluating artwork...")
                    critic_feedback = self.critic.evaluate_artwork(
                        prev_canvas, 
                        current_goal,
                        self.critic.evaluation_history[-3:] if len(self.critic.evaluation_history) > 3 else None
                    )
                    
                    print(f"📊 Critic Score: {critic_feedback.overall_score}/10")
                    print(f"💪 Strengths: {', '.join(critic_feedback.strengths[:2])}")  # Show top 2
                    print(f"⚠️ Areas to improve: {', '.join(critic_feedback.weaknesses[:2])}")  # Show top 2
                    
                    # Check if critic suggests stopping
                    if not critic_feedback.continue_drawing and critic_feedback.overall_score >= 7.5:
                        print("🎉 Critic suggests the artwork is complete! Finishing exploration.")
                        break
                
                # Actor makes decision based on critic feedback
                print("🎭 Actor deciding next action...")
                actor_decision = self.actor.decide_with_feedback(
                    prev_canvas, 
                    critic_feedback, 
                    current_goal
                )
                
                print(f"🎨 Actor Decision: {actor_decision.action.brush} brush with {actor_decision.action.color}")
                print(f"💭 Artistic Intent: {actor_decision.artistic_intent}")
                print(f"🔮 Confidence: {actor_decision.confidence:.2f}")
                
                # Execute the action
                try:
                    self.painter.bridge.execute_action(actor_decision.action)
                    
                    # Capture result
                    result_canvas = os.path.join(output_dir, f"stage_{stage}_canvas.png")
                    self.painter.bridge.capture_canvas(result_canvas)
                    
                    # Log the exploration step
                    self.exploration_log.append({
                        "stage": stage,
                        "goal": current_goal,
                        "actor_decision": {
                            "brush": actor_decision.action.brush,
                            "color": actor_decision.action.color,
                            "confidence": actor_decision.confidence,
                            "reasoning": actor_decision.action.reasoning
                        },
                        "critic_feedback": {
                            "score": critic_feedback.overall_score if critic_feedback else None,
                            "reasoning": critic_feedback.reasoning if critic_feedback else None
                        } if critic_feedback else None
                    })
                    
                    # Occasionally change artistic goal to keep exploration dynamic
                    if stage % 8 == 0 and stage < max_stages - 5:
                        current_goal = random.choice(self.artistic_goals)
                        print(f"🔄 New Artistic Goal: {current_goal}")
                    
                except Exception as e:
                    print(f"❌ Error executing action: {e}")
                    continue
            
            # Final evaluation
            final_canvas = os.path.join(output_dir, f"stage_{self.current_stage}_canvas.png")
            final_feedback = self.critic.evaluate_artwork(final_canvas, "Final artwork evaluation")
            
            print(f"\n🏆 === FINAL EVALUATION ===")
            print(f"📊 Final Score: {final_feedback.overall_score}/10")
            print(f"💪 Final Strengths: {', '.join(final_feedback.strengths)}")
            print(f"🎯 Final Reasoning: {final_feedback.reasoning}")
            
            # Save exploration log
            log_file = os.path.join(output_dir, "exploration_log.json")
            with open(log_file, 'w') as f:
                json.dump({
                    "total_stages": self.current_stage,
                    "final_score": final_feedback.overall_score,
                    "exploration_log": self.exploration_log
                }, f, indent=2)
            
            print(f"\n✅ Actor-Critic exploration completed!")
            print(f"📁 Results saved in: {output_dir}")
            print(f"📊 Total stages: {self.current_stage}")
            
        except KeyboardInterrupt:
            print("\n⚠️ Exploration interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during exploration: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.painter.close()

def main():
    """Main entry point for the actor-critic explorer"""
    
    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: Please set ANTHROPIC_API_KEY in your .env file")
        sys.exit(1)
    
    # Initialize and run explorer
    explorer = ActorCriticExplorer(api_key)
    explorer.explore_brushes(max_stages=30)

if __name__ == "__main__":
    main() 