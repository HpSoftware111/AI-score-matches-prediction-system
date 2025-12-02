"""
DeepSeek API Client for generating predictions
"""
import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """Client for interacting with DeepSeek API"""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        
    def _make_request(self, prompt, model="deepseek-chat", return_full_response=False):
        """
        Make API request to DeepSeek
        
        Args:
            prompt: The user prompt to send
            model: The model to use (default: deepseek-chat)
            return_full_response: If True, return full API response instead of just the prediction digit
        
        Returns:
            If return_full_response=False: Single digit ('3', '1', or '0') or None
            If return_full_response=True: Full response dictionary with request and response data
        """
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a sport prediction expert. Always respond with a single digit: 3 for Team A win, 1 for draw, 0 for Team B win.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 10
        }
        
        # Log the request data
        logger.info(f"Sending request to DeepSeek API: {self.api_url}")
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Log the response
            logger.info(f"Received response from DeepSeek API")
            logger.debug(f"Response data: {json.dumps(data, indent=2)}")
            
            if return_full_response:
                return {
                    'success': True,
                    'request': {
                        'url': self.api_url,
                        'model': model,
                        'prompt': prompt,
                        'payload': payload
                    },
                    'response': data,
                    'raw_content': data.get('choices', [{}])[0].get('message', {}).get('content', '') if data.get('choices') else ''
                }
            
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content'].strip()
                # Extract single digit from response
                for char in content:
                    if char in ['3', '1', '0']:
                        logger.info(f"Extracted prediction: {char}")
                        return char
                logger.warning(f"Unexpected response format: {content}")
                return None
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DeepSeek API error: {e}")
            if return_full_response:
                return {
                    'success': False,
                    'error': str(e),
                    'request': {
                        'url': self.api_url,
                        'model': model,
                        'prompt': prompt,
                        'payload': payload
                    }
                }
            return None
    
    def generate_baseline_prediction(self, match):
        """Generate baseline prediction based on probabilities"""
        prompt = f"""Match: {match.team_a} vs {match.team_b}
Probabilities: {match.team_a} {match.prob_a_percent}%, {match.team_b} {match.prob_b_percent}%
Draw probability: {match.draw_prob_percent}%

Rules:
- If {match.team_a} probability is significantly higher (difference > 15%) → 3
- If {match.team_b} probability is significantly higher (difference > 15%) → 0
- If probabilities are close (difference ≤ 15%) → 1

Output: single digit (3, 1, or 0)"""
        
        return self._make_request(prompt)
    
    def generate_profitable_prediction(self, match):
        """Generate profitable prediction comparing odds vs implied probability"""
        implied_prob_a = match.implied_prob_a
        implied_prob_b = match.implied_prob_b
        
        prompt = f"""Match: {match.team_a} vs {match.team_b}
Actual Probabilities: {match.team_a} {match.prob_a_percent}%, {match.team_b} {match.prob_b_percent}%
Odds: {match.team_a} {match.odds_a}, {match.team_b} {match.odds_b}
Implied Probabilities from Odds: {match.team_a} {implied_prob_a*100:.2f}%, {match.team_b} {implied_prob_b*100:.2f}%

Rules:
- If actual probability > implied probability by at least 10% → that team is undervalued
- If {match.team_a} is undervalued → 3
- If {match.team_b} is undervalued → 0
- If neither team is significantly undervalued → 1

Output: single digit (3, 1, or 0)"""
        
        return self._make_request(prompt)
    
    def get_full_prediction_response(self, match, prediction_type='baseline'):
        """
        Get full API response from DeepSeek for a match prediction
        
        Args:
            match: Match object
            prediction_type: 'baseline', 'profitable', or 'balanced'
        
        Returns:
            Dictionary with full request and response data
        """
        if prediction_type == 'baseline':
            prompt = f"""Match: {match.team_a} vs {match.team_b}
Probabilities: {match.team_a} {match.prob_a_percent}%, {match.team_b} {match.prob_b_percent}%
Draw probability: {match.draw_prob_percent}%

Rules:
- If {match.team_a} probability is significantly higher (difference > 15%) → 3
- If {match.team_b} probability is significantly higher (difference > 15%) → 0
- If probabilities are close (difference ≤ 15%) → 1

Output: single digit (3, 1, or 0)"""
        elif prediction_type == 'profitable':
            implied_prob_a = match.implied_prob_a
            implied_prob_b = match.implied_prob_b
            prompt = f"""Match: {match.team_a} vs {match.team_b}
Actual Probabilities: {match.team_a} {match.prob_a_percent}%, {match.team_b} {match.prob_b_percent}%
Odds: {match.team_a} {match.odds_a}, {match.team_b} {match.odds_b}
Implied Probabilities from Odds: {match.team_a} {implied_prob_a*100:.2f}%, {match.team_b} {implied_prob_b*100:.2f}%

Rules:
- If actual probability > implied probability by at least 10% → that team is undervalued
- If {match.team_a} is undervalued → 3
- If {match.team_b} is undervalued → 0
- If neither team is significantly undervalued → 1

Output: single digit (3, 1, or 0)"""
        else:  # balanced
            implied_prob_a = match.implied_prob_a
            implied_prob_b = match.implied_prob_b
            prompt = f"""Match: {match.team_a} vs {match.team_b}
Actual Probabilities: {match.team_a} {match.prob_a_percent}%, {match.team_b} {match.prob_b_percent}%
Odds: {match.team_a} {match.odds_a}, {match.team_b} {match.odds_b}
Implied Probabilities: {match.team_a} {implied_prob_a*100:.2f}%, {match.team_b} {implied_prob_b*100:.2f}%

Rules:
- Combine actual probability and odds alignment
- If {match.team_a} has high actual probability (>45%) AND good odds value → 3
- If {match.team_b} has high actual probability (>45%) AND good odds value → 0
- If probabilities and odds don't align clearly → 1

Output: single digit (3, 1, or 0)"""
        
        return self._make_request(prompt, return_full_response=True)
    
    def generate_balanced_prediction(self, match):
        """Generate balanced prediction combining probability and odds"""
        implied_prob_a = match.implied_prob_a
        implied_prob_b = match.implied_prob_b
        
        prompt = f"""Match: {match.team_a} vs {match.team_b}
Actual Probabilities: {match.team_a} {match.prob_a_percent}%, {match.team_b} {match.prob_b_percent}%
Odds: {match.team_a} {match.odds_a}, {match.team_b} {match.odds_b}
Implied Probabilities: {match.team_a} {implied_prob_a*100:.2f}%, {match.team_b} {implied_prob_b*100:.2f}%

Rules:
- Combine actual probability and odds alignment
- If {match.team_a} has high actual probability (>45%) AND good odds value → 3
- If {match.team_b} has high actual probability (>45%) AND good odds value → 0
- If probabilities and odds don't align clearly → 1

Output: single digit (3, 1, or 0)"""
        
        return self._make_request(prompt)

