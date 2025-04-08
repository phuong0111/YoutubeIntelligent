import os
import re
import json
from typing import Dict, List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class VietnameseDangerousContentDetector:
    """
    A detector for dangerous content in Vietnamese text using the ViHateT5 transformer model.
    """
    
    def __init__(self, model_name: str = "tarudesu/ViHateT5-base-HSD"):
        """
        Initialize the detector with the ViHateT5 model.
        
        Args:
            model_name: Name of the pretrained model to use
        """
        # Load the transformer model and tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Set the hate spans detection prefix
        self.prefix = "hate-spans-detection"
    
    def generate_output(self, input_text: str) -> str:
        """
        Generate output using the transformer model with hate spans detection.
        
        Args:
            input_text: The text to analyze
            
        Returns:
            The model's output with hate spans marked
        """
        # Add prefix to input
        prefixed_input_text = f"{self.prefix}: {input_text}"
        
        # Tokenize input text
        input_ids = self.tokenizer.encode(prefixed_input_text, return_tensors="pt")
        
        # Generate output
        output_ids = self.model.generate(input_ids, max_length=256)
        
        # Decode the generated output
        output_text = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
        
        return output_text
    
    def analyze_text(self, text: str, min_severity: int = 1) -> Dict:
        """
        Analyze text and identify dangerous content.
        
        Args:
            text: The Vietnamese text to analyze
            min_severity: Minimum severity level (ignored, kept for API compatibility)
            
        Returns:
            Dictionary with analysis results
        """
        # Get model output with hate spans
        result = self.generate_output(text)
        
        # Extract hate spans (text within [hate] tags)
        pattern = r'\[hate\](.*?)\[hate\]'
        hate_spans = re.findall(pattern, result)
        
        # Determine if text is dangerous based on presence of hate spans
        is_dangerous = len(hate_spans) > 0
        
        # Calculate severity based on number of hate spans (simple heuristic)
        severity = min(len(hate_spans) + 1, 4) if is_dangerous else 0
        
        # Create results dictionary in the original format
        results = {
            "is_dangerous": is_dangerous,
            "matches": {},
            "highest_severity": severity
        }
        
        if is_dangerous:
            results["matches"]["hate_speech"] = {
                "keywords": hate_spans,
                "severity": severity,
                "count": len(hate_spans)
            }
        
        return results
    
    def analyze_title(self, title: str, min_severity: int = 1) -> Dict:
        """
        Analyze video title for dangerous content.
        
        Args:
            title: The video title to analyze
            min_severity: Minimum severity level (ignored, kept for API compatibility)
            
        Returns:
            Dictionary with analysis results
        """
        results = self.analyze_text(title, min_severity)
        results["content_type"] = "title"
        return results
    
    def analyze_comments(self, comments: List[Dict], min_severity: int = 1) -> Dict:
        """
        Analyze a list of comments for dangerous content.
        
        Args:
            comments: List of comment dictionaries with 'text' key
            min_severity: Minimum severity level (ignored, kept for API compatibility)
            
        Returns:
            Dictionary with analysis results
        """
        combined_results = {
            "is_dangerous": False,
            "highest_severity": 0,
            "content_type": "comments",
            "total_comments": len(comments),
            "dangerous_comments": [],
            "dangerous_comment_count": 0
        }
        
        for i, comment in enumerate(comments):
            comment_text = comment.get('text', '') or comment.get('comment_text', '')
            if not comment_text:
                continue
                
            # Analyze individual comment
            result = self.analyze_text(comment_text, min_severity)
            
            if result["is_dangerous"]:
                # Add this comment to the dangerous comments list
                dangerous_comment = {
                    "index": i,
                    "comment_data": comment,
                    "analysis": result
                }
                combined_results["dangerous_comments"].append(dangerous_comment)
                combined_results["dangerous_comment_count"] += 1
                combined_results["is_dangerous"] = True
                combined_results["highest_severity"] = max(
                    combined_results["highest_severity"], 
                    result["highest_severity"]
                )
        
        return combined_results


# Example usage
if __name__ == "__main__":
    # Create a detector
    detector = VietnameseDangerousContentDetector()
    
    # Example text analysis
    sample = "Tôi ghét bạn vl luôn!"
    
    # Analyze the text
    results = detector.analyze_text(sample)
    
    # Print the formatted result
    print(json.dumps(results, ensure_ascii=False, indent=2))
    
    # Expected output would look like:
    # {
    #   "is_dangerous": true,
    #   "matches": {
    #     "hate_speech": {
    #       "keywords": ["vl"],
    #       "severity": 2,
    #       "count": 1
    #     }
    #   },
    #   "highest_severity": 2
    # }