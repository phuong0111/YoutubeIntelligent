import os
import re
import json
from typing import Dict, List, Optional


class VietnameseDangerousContentDetector:
    """
    A rule-based system for detecting dangerous content in Vietnamese text.
    Supports multiple categories of dangerous content with configurable severity levels.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the detector with default or custom configuration.
        
        Args:
            config_path: Optional path to a JSON configuration file
        """
        # Default keyword categories with varying severity levels
        self.default_keywords = {
            "violence": {
                "keywords": ["giết người", "đánh nhau", "bạo lực", "tấn công", "đâm", "chém", 
                            "hành hung", "đe dọa", "trả thù", "hành quyết", "sát hại"],
                "severity": 3
            },
            "terrorism": {
                "keywords": ["khủng bố", "bom", "đánh bom", "tự sát", "phá hoại", 
                            "cực đoan", "bạo động", "khủng bố", "kích động"],
                "severity": 4
            },
            "weapons": {
                "keywords": ["súng", "đạn", "vũ khí", "dao", "thuốc nổ", "mìn", 
                            "lựu đạn", "vũ trang", "chất nổ"],
                "severity": 2
            },
            "drugs": {
                "keywords": ["ma túy", "heroin", "cần sa", "cocaine", "thuốc lắc", 
                            "chất gây nghiện", "tiêm chích", "chất kích thích"],
                "severity": 2
            },
            "political_extremism": {
                "keywords": ["lật đổ", "phản động", "chống phá", "phá hoại", 
                            "chống đối", "âm mưu", "gây rối", "bạo loạn"],
                "severity": 3
            },
            "hate_speech": {
                "keywords": ["nông cạn", "bức xúc", "thù hằn", "kỳ thị", "phân biệt", 
                            "ghét bỏ", "xúc phạm", "nhục mạ", "nhạo báng"],
                "severity": 1
            }
        }
        
        # Load custom configuration if provided
        self.keywords = self.default_keywords
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    custom_config = json.load(f)
                    self.keywords.update(custom_config)
            except Exception as e:
                print(f"Lỗi khi tải tệp cấu hình: {e}")
                print("Sử dụng cấu hình mặc định")
        
        # Compile regex patterns for each category for faster matching
        self.patterns = {}
        for category, data in self.keywords.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in data["keywords"]) + r')\b'
            self.patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def analyze_text(self, text: str, min_severity: int = 1) -> Dict:
        """
        Analyze text and identify dangerous content above the minimum severity threshold.
        
        Args:
            text: The Vietnamese text to analyze
            min_severity: Minimum severity level to report (1-4)
            
        Returns:
            Dictionary with analysis results and matched content
        """
        results = {
            "is_dangerous": False,
            "matches": {},
            "highest_severity": 0,
            "dangerous_categories": []
        }
        
        # Check each category
        for category, pattern in self.patterns.items():
            severity = self.keywords[category]["severity"]
            if severity < min_severity:
                continue
                
            matches = pattern.findall(text)
            if matches:
                unique_matches = list(set(matches))
                results["matches"][category] = {
                    "keywords": unique_matches,
                    "severity": severity,
                    "count": len(matches)
                }
                results["is_dangerous"] = True
                results["dangerous_categories"].append(category)
                results["highest_severity"] = max(results["highest_severity"], severity)
        
        return results
    
    def analyze_title(self, title: str, min_severity: int = 1) -> Dict:
        """
        Analyze video title for dangerous content.
        
        Args:
            title: The video title to analyze
            min_severity: Minimum severity level to report
            
        Returns:
            Dictionary with analysis results
        """
        # Use the same analysis method but mark it specifically for title
        results = self.analyze_text(title, min_severity)
        results["content_type"] = "title"
        return results
    
    def analyze_comments(self, comments: List[Dict], min_severity: int = 1) -> Dict:
        """
        Analyze a list of comments for dangerous content.
        
        Args:
            comments: List of comment dictionaries with 'text' key
            min_severity: Minimum severity level to report
            
        Returns:
            Dictionary with analysis results and dangerous comments
        """
        combined_results = {
            "is_dangerous": False,
            "highest_severity": 0,
            "dangerous_categories": set(),
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
                
                # Add all dangerous categories found
                for category in result["dangerous_categories"]:
                    combined_results["dangerous_categories"].add(category)
        
        # Convert set to list for JSON serialization
        combined_results["dangerous_categories"] = list(combined_results["dangerous_categories"])
        
        return combined_results
    
    def format_report(self, results: Dict, verbose: bool = False) -> str:
        """
        Format analysis results into a human-readable report.
        
        Args:
            results: Analysis results from analyze_text
            verbose: Whether to include detailed match information
            
        Returns:
            Formatted report as a string
        """
        content_type = results.get("content_type", "content")
        
        if results.get("is_dangerous", False):
            report = f"🔴 Phát hiện nội dung nguy hiểm trong {content_type}!\n"
            report += f"Mức độ nghiêm trọng: {results['highest_severity']}/4\n\n"
            
            if verbose:
                report += "Chi tiết:\n"
                
                if content_type == "comments":
                    report += f"Phát hiện {results['dangerous_comment_count']} bình luận nguy hiểm " \
                             f"trong tổng số {results['total_comments']} bình luận.\n\n"
                    
                    for i, comment in enumerate(results["dangerous_comments"][:5]):  # Limit to first 5
                        report += f"Bình luận #{i+1}:\n"
                        report += f"Người dùng: {comment['comment_data'].get('author', 'Unknown')}\n"
                        report += f"Nội dung: {comment['comment_data'].get('text', '')[:100]}...\n"
                        report += f"Mức độ nghiêm trọng: {comment['analysis']['highest_severity']}/4\n"
                        report += f"Danh mục: {', '.join(comment['analysis']['dangerous_categories'])}\n\n"
                    
                    if len(results["dangerous_comments"]) > 5:
                        report += f"... và {len(results['dangerous_comments']) - 5} bình luận nguy hiểm khác.\n"
                
                else:
                    # For title or transcription
                    for category in results["dangerous_categories"]:
                        if "matches" in results and category in results["matches"]:
                            matches = results["matches"][category]
                            report += f"- {category.upper()} (Mức độ: {matches['severity']}/4)\n"
                            report += f"  Từ khóa: {', '.join(matches['keywords'])}\n"
                            report += f"  Số lần xuất hiện: {matches['count']}\n"
        else:
            report = f"✅ Không phát hiện nội dung nguy hiểm trong {content_type}"
        
        return report
    
    def add_custom_category(self, category_name: str, keywords: List[str], severity: int = 2) -> None:
        """
        Add a custom category of dangerous content with keywords and severity.
        
        Args:
            category_name: Name of the new category
            keywords: List of keywords for the category
            severity: Severity level (1-4)
        """
        if severity < 1 or severity > 4:
            raise ValueError("Mức độ nghiêm trọng phải từ 1 đến 4")
            
        self.keywords[category_name] = {
            "keywords": keywords,
            "severity": severity
        }
        
        # Update the regex pattern for the new category
        pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
        self.patterns[category_name] = re.compile(pattern, re.IGNORECASE)
    
    def save_config(self, config_path: str) -> None:
        """
        Save the current keyword configuration to a file.
        
        Args:
            config_path: Path to save the configuration JSON file
        """
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu cấu hình thành công vào {config_path}")
        except Exception as e:
            print(f"Lỗi khi lưu cấu hình: {e}")


# Example usage
if __name__ == "__main__":
    # Create a detector with default configuration
    detector = VietnameseDangerousContentDetector()
    
    # Add a custom category if needed
    detector.add_custom_category(
        "financial_crime", 
        ["rửa tiền", "lừa đảo", "chiếm đoạt", "biển thủ", "trốn thuế"],
        severity=2
    )
    
    # Example text analysis
    text = """
    Các đối tượng đã lên kế hoạch tấn công vào tòa nhà chính phủ và sử dụng
    bom tự chế để gây ra hoảng loạn. Chúng còn buôn bán ma túy để gây quỹ cho
    hoạt động khủng bố.
    """
    
    # Analyze the text
    results = detector.analyze_text(text)
    
    # Print the formatted report
    print(detector.format_report(results, verbose=True))
    
    # Example title analysis
    title = "Các đối tượng tấn công và đe dọa cảnh sát"
    title_results = detector.analyze_title(title)
    print("\nTitle Analysis:")
    print(detector.format_report(title_results, verbose=True))
    
    # Example comments analysis
    comments = [
        {"author": "User1", "text": "Bài viết hay và bổ ích"},
        {"author": "User2", "text": "Tôi sẽ tấn công bất kỳ ai chống đối tôi với súng của tôi"},
        {"author": "User3", "text": "Quá nhiều bạo lực trong xã hội ngày nay"}
    ]
    comment_results = detector.analyze_comments(comments)
    print("\nComments Analysis:")
    print(detector.format_report(comment_results, verbose=True))


# Simple function example without using the class
def check_dangerous_content(text, min_severity=1):
    """
    Simple function to check for dangerous content in Vietnamese text.
    
    Args:
        text: Text to analyze
        min_severity: Minimum severity level (1-4)
        
    Returns:
        Tuple of (is_dangerous, report_string)
    """
    detector = VietnameseDangerousContentDetector()
    results = detector.analyze_text(text, min_severity)
    report = detector.format_report(results, verbose=True)
    return results["is_dangerous"], report