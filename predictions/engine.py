"""
Prediction Engine: Rule-based prediction logic
"""
from .deepseek_client import DeepSeekClient
import logging

logger = logging.getLogger(__name__)


class PredictionEngine:
    """Engine for generating predictions using rules and AI"""
    
    def __init__(self, use_ai=True):
        self.use_ai = use_ai
        self.ai_client = DeepSeekClient() if use_ai else None
        self.threshold = 0.15  # 15% difference threshold for "close" matches
    
    def calculate_baseline_prediction(self, match):
        """
        Baseline Prediction:
        Rule: Higher probability → 1 (Team A), 3 (Team B), close → 0
        """
        prob_diff = abs(match.prob_a - match.prob_b)
        
        if prob_diff <= self.threshold:
            return '0'  # Close match → draw
        elif match.prob_a > match.prob_b:
            return '1'  # Team A higher
        else:
            return '3'  # Team B higher
    
    def calculate_profitable_prediction(self, match):
        """
        Profitable Prediction:
        Rule: Compare implied probability vs sportsbook odds
        If odds undervalue a team → mark that team
        """
        implied_prob_a = match.implied_prob_a
        implied_prob_b = match.implied_prob_b
        
        # Calculate value: actual_prob - implied_prob
        value_a = match.prob_a - implied_prob_a
        value_b = match.prob_b - implied_prob_b
        value_threshold = 0.10  # 10% minimum value
        
        if value_a >= value_threshold and value_a > value_b:
            return '1'  # Team A undervalued
        elif value_b >= value_threshold and value_b > value_a:
            return '3'  # Team B undervalued
        else:
            return '0'  # No clear value
    
    def calculate_balanced_prediction(self, match):
        """
        Balanced Prediction:
        Rule: Combine probability + odds
        If both align → pick team, else → 0
        """
        implied_prob_a = match.implied_prob_a
        implied_prob_b = match.implied_prob_b
        
        # Team A: High actual prob (>45%) AND good odds value (>5% advantage)
        team_a_score = 0
        if match.prob_a > 0.45:
            team_a_score += 1
        if match.prob_a > implied_prob_a + 0.05:
            team_a_score += 1
        
        # Team B: High actual prob (>45%) AND good odds value (>5% advantage)
        team_b_score = 0
        if match.prob_b > 0.45:
            team_b_score += 1
        if match.prob_b > implied_prob_b + 0.05:
            team_b_score += 1
        
        if team_a_score >= 2 and team_a_score > team_b_score:
            return '1'  # Team A clearly aligned
        elif team_b_score >= 2 and team_b_score > team_a_score:
            return '3'  # Team B clearly aligned
        else:
            return '0'  # Not clearly aligned
    
    def generate_prediction(self, match, use_ai=False):
        """
        Generate all three prediction types for a match
        """
        # Calculate rule-based predictions
        baseline = self.calculate_baseline_prediction(match)
        profitable = self.calculate_profitable_prediction(match)
        balanced = self.calculate_balanced_prediction(match)
        
        # Generate AI predictions if enabled
        ai_baseline = None
        ai_profitable = None
        ai_balanced = None
        
        if use_ai and self.ai_client:
            try:
                ai_baseline = self.ai_client.generate_baseline_prediction(match)
                ai_profitable = self.ai_client.generate_profitable_prediction(match)
                ai_balanced = self.ai_client.generate_balanced_prediction(match)
            except Exception as e:
                logger.error(f"Error generating AI predictions: {e}")
        
        return {
            'baseline': baseline,
            'profitable': profitable,
            'balanced': balanced,
            'ai_baseline': ai_baseline,
            'ai_profitable': ai_profitable,
            'ai_balanced': ai_balanced
        }

