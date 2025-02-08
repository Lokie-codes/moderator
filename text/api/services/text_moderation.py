# services/text_moderation.py

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from dataclasses import dataclass
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone

# Configuration Constants
VALID_CATEGORIES = {
    # Content Type Categories
    'PROFANITY',
    'HATE_SPEECH',
    'HARASSMENT',
    'VIOLENCE',
    'SEXUAL_CONTENT',
    'DISCRIMINATION',
    'THREAT',
    'SPAM',
    
    # Additional Safety Categories
    'SELF_HARM',
    'SUICIDE',
    'EATING_DISORDERS',
    'SUBSTANCE_ABUSE',
    'GROOMING',
    'EXTREMISM',
    
    # Platform Integrity Categories
    'MISINFORMATION',
    'DISINFORMATION',
    'IMPERSONATION',
    'FRAUDULENT_ACTIVITY',
    'COUNTERFEIT_GOODS',
    
    # Personal Information
    'PERSONAL_INFO',
    'DOXXING',
    'PRIVACY_VIOLATION',
    
    # Community Standards
    'BULLYING',
    'TROLLING',
    'INFLAMMATORY',
    'GRAPHIC_CONTENT',
    
    # Financial Content
    'GAMBLING',
    'SCAM',
    'UNAUTHORIZED_MARKETING',
    
    # Other Categories
    'COPYRIGHT_VIOLATION',
    'TRADEMARK_VIOLATION',
    'AGE_INAPPROPRIATE',
    'CHILD_SAFETY',
    'COORDINATED_HARM'
}

DEFAULT_CATEGORIES = ['PROFANITY', 'HATE_SPEECH', 'HARASSMENT']
VALID_SENSITIVITY_LEVELS = {'LOW', 'MEDIUM', 'HIGH'}

@dataclass
class ModerationResult:
    text: str
    is_inappropriate: bool
    confidence: float
    categories: Dict[str, float]

class TextModerationService:
    def __init__(
        self,
        model_name: str = "facebook/roberta-hate-speech-dynabench-r4-target",
        threshold: float = 0.8
    ):
        self.threshold = threshold
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger = logging.getLogger(__name__)
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(self.device)
            self.model.eval()
            self.logger.info(f"Model loaded successfully on {self.device}")
        except Exception as e:
            self.logger.error(f"Error loading model: {str(e)}")
            raise

    def validate_categories(self, categories: Optional[List[str]] = None) -> List[str]:
        """Validate and return categories, using defaults if none provided."""
        if not categories:
            return DEFAULT_CATEGORIES
            
        valid_cats = [cat for cat in categories if cat in VALID_CATEGORIES]
        return valid_cats if valid_cats else DEFAULT_CATEGORIES

    def validate_request(self, request_data: Dict) -> tuple[bool, Optional[str]]:
        """Validate the incoming request structure."""
        try:
            if 'content' not in request_data:
                return False, "Missing 'content' section"
            if 'text' not in request_data['content']:
                return False, "Missing 'text' field in content"

            config = request_data.get('configuration', {})
            if config:
                sensitivity = config.get('sensitivityLevel')
                if sensitivity and sensitivity not in VALID_SENSITIVITY_LEVELS:
                    return False, f"Invalid sensitivity level. Must be one of {VALID_SENSITIVITY_LEVELS}"

            return True, None
        except Exception as e:
            self.logger.error(f"Request validation error: {str(e)}")
            return False, str(e)

    def _preprocess_text(self, text: str) -> str:
        """Clean and prepare text for moderation."""
        return text.strip().lower()

    def moderate_text(self, text: str) -> ModerationResult:
        """Moderate a single piece of text."""
        try:
            processed_text = self._preprocess_text(text)
            
            inputs = self.tokenizer(
                processed_text,
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(self.device)

            with torch.no_grad():
                outputs = self.model(**inputs)
                probabilities = torch.nn.functional.softmax(outputs.logits, dim=1)
                
            probs = probabilities.cpu().numpy()[0]
            
            categories = {
                "HATE_SPEECH": float(probs[1]),
                "PROFANITY": float(probs[1] > 0.5),
                "HARASSMENT": float(probs[1] > 0.7)
            }
            
            is_inappropriate = any(score > self.threshold for score in categories.values())
            
            return ModerationResult(
                text=text,
                is_inappropriate=is_inappropriate,
                confidence=float(max(probs)),
                categories=categories
            )
            
        except Exception as e:
            self.logger.error(f"Error moderating text: {str(e)}")
            raise

    def format_response(self, moderation_result: Dict, request_data: Dict, processing_time: int) -> Dict:
        """Format the moderation result according to the specified response structure."""
        request_id = request_data.get('metadata', {}).get('requestId', 'unknown')
        current_time = datetime.now(timezone.utc).isoformat()

        response = {
            "status": "SUCCESS",
            "requestId": request_id,
            "timestamp": current_time,
            "processingTime": processing_time,
            "result": {
                "decision": "FLAGGED" if moderation_result['is_inappropriate'] else "ACCEPTED",
                "confidence": moderation_result['confidence'],
                "analysis": {
                    "language": request_data['content'].get('language', 'en'),
                    "toxicity": max(moderation_result['categories'].values()),
                    "categories": {}
                },
                "metadata": {
                    "processedAt": current_time,
                    "modelVersion": "v1.0"
                }
            }
        }

        for category, score in moderation_result['categories'].items():
            response["result"]["analysis"]["categories"][category] = {
                "score": score,
                "verdict": "FLAGGED" if score > 0.8 else "ACCEPTED",
                "violations": []
            }

        return response