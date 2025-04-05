from typing import Dict, List, Any, Optional, Tuple
import json
import time
import os
from datetime import datetime
import traceback
import re

# Import our database manager
from db.db_setup import DatabaseManager

# Import the original modules
from modules.scrape import YouTubeChannelScraper
from modules.detect import VietnameseDangerousContentDetector
from utils import get_filename_without_extension

class ChannelManager:
    """Manages YouTube channel data and operations."""
    
    def __init__(self, db_path: str, headless: bool = True):
        """
        Initialize the channel manager.
        
        Args:
            db_path: Path to SQLite database file
            headless: Whether to run Chrome in headless mode
        """
        self.db = DatabaseManager(db_path)
        self.scraper = YouTubeChannelScraper(headless=headless)
    
    def close(self):
        """Close resources."""
        if self.scraper:
            self.scraper.close()
        if self.db:
            self.db.close()
    
    def add_channel(self, channel_input: str) -> Optional[int]:
        """
        Add a YouTube channel to the database.
        
        Args:
            channel_input: Channel name, URL, or @username
            
        Returns:
            ID of the added channel, or None if failed
        """
        task_id = self.db.create_task("scrape", None, "channel")
        
        try:
            self.db.update_task_status(task_id, "in_progress")
            
            # Search for the channel
            channel_url = self.scraper.search_channel(channel_input)
            
            if not channel_url:
                self.db.update_task_status(task_id, "failed", f"Could not find channel: {channel_input}")
                return None
            
            # Get channel information
            channel_info = self.scraper.get_channel_info(channel_url)
            
            # Check if channel already exists
            existing = self.db.fetchone(
                "SELECT id FROM channels WHERE channel_id = ?", 
                (channel_info["channel_id"],)
            )
            
            if existing:
                channel_id = existing[0]
                # Update existing channel
                self.db.update(
                    "channels",
                    {
                        "channel_name": channel_info["channel_name"],
                        "subscribers": channel_info["subscribers"],
                        "description": channel_info["description"],
                        "url": channel_info["url"],
                        "thumbnail": channel_info["thumbnail"],
                        "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    },
                    "id = ?",
                    (channel_id,)
                )
            else:
                # Insert new channel
                channel_id = self.db.insert("channels", {
                    "channel_id": channel_info["channel_id"],
                    "channel_name": channel_info["channel_name"],
                    "subscribers": channel_info["subscribers"],
                    "description": channel_info["description"],
                    "url": channel_info["url"],
                    "thumbnail": channel_info["thumbnail"]
                })
            
            self.db.update_task_status(task_id, "completed")
            return channel_id
            
        except Exception as e:
            error_msg = f"Error adding channel: {e}\n{traceback.format_exc()}"
            print(error_msg)
            self.db.update_task_status(task_id, "failed", error_msg)
            return None
    
    def scrape_channel_videos(self, channel_id: int, max_videos: int = 20) -> List[int]:
        """
        Scrape videos from a YouTube channel and store them in the database.
        
        Args:
            channel_id: Database ID of the channel
            max_videos: Maximum number of videos to scrape
            
        Returns:
            List of video IDs added to the database
        """
        task_id = self.db.create_task("scrape", channel_id, "channel_videos")
        added_video_ids = []
        
        try:
            self.db.update_task_status(task_id, "in_progress")
            
            # Get channel URL from database
            channel_data = self.db.fetchone(
                "SELECT url FROM channels WHERE id = ?", 
                (channel_id,)
            )
            
            if not channel_data:
                self.db.update_task_status(task_id, "failed", f"Channel with ID {channel_id} not found")
                return []
            
            channel_url = channel_data[0]
            
            # Scrape videos from the channel
            videos = self.scraper.get_channel_videos(channel_url, max_videos)
            
            # Initialize content detector
            detector = VietnameseDangerousContentDetector()
            
            # Add each video to the database
            for video in videos:
                # Check if video already exists
                existing = self.db.fetchone(
                    "SELECT id FROM videos WHERE video_id = ?", 
                    (video["video_id"],)
                )
                
                if existing:
                    # Video exists, update it
                    video_db_id = existing[0]
                    self.db.update(
                        "videos",
                        {
                            "title": video["title"],
                            "views": video["views"],
                            "upload_date": video["upload_date"]
                        },
                        "id = ?",
                        (video_db_id,)
                    )
                else:
                    # Get detailed video information
                    video_details = self.scraper.get_video_details(video["url"])
                    
                    # Analyze the video title for dangerous content
                    title_analysis = detector.analyze_title(video["title"])
                    
                    # Insert new video
                    video_db_id = self.db.insert("videos", {
                        "video_id": video["video_id"],
                        "channel_id": channel_id,
                        "title": video["title"],
                        "url": video["url"],
                        "views": video["views"],
                        "upload_date": video["upload_date"],
                        "likes": video_details.get("likes", 0),
                        "description": video_details.get("description", ""),
                        "thumbnail": video_details.get("thumbnail", "")
                    })
                    
                    # If title contains dangerous content, store the analysis
                    if title_analysis["is_dangerous"]:
                        # Insert title analysis as a special type of content analysis
                        analysis_id = self.db.insert("content_analysis", {
                            "transcription_id": None,  # Not associated with a transcription
                            "video_id": video_db_id,  # Directly associated with video
                            "content_type": "title",
                            "is_dangerous": 1,
                            "highest_severity": title_analysis["highest_severity"],
                            "analysis_results": json.dumps(title_analysis, ensure_ascii=False)
                        })
                        
                        # Insert detected categories
                        for category in title_analysis["dangerous_categories"]:
                            if category in title_analysis["matches"]:
                                self.db.insert("analysis_categories", {
                                    "analysis_id": analysis_id,
                                    "category_name": category,
                                    "severity": title_analysis["matches"][category]["severity"],
                                    "keywords": json.dumps(title_analysis["matches"][category]["keywords"], ensure_ascii=False),
                                    "count": title_analysis["matches"][category]["count"]
                                })
                
                added_video_ids.append(video_db_id)
            
            self.db.update_task_status(task_id, "completed")
            return added_video_ids
            
        except Exception as e:
            error_msg = f"Error scraping channel videos: {e}\n{traceback.format_exc()}"
            print(error_msg)
            self.db.update_task_status(task_id, "failed", error_msg)
            return []
    
    def scrape_video_comments(self, video_db_id: int, max_comments: int = 20) -> int:
        """
        Scrape comments from a YouTube video and store them in the database.
        
        Args:
            video_db_id: Database ID of the video
            max_comments: Maximum number of comments to scrape
            
        Returns:
            Number of comments added
        """
        task_id = self.db.create_task("scrape", video_db_id, "video_comments")
        
        try:
            self.db.update_task_status(task_id, "in_progress")
            
            # Get video URL from database
            video_data = self.db.fetchone(
                "SELECT url FROM videos WHERE id = ?", 
                (video_db_id,)
            )
            
            if not video_data:
                self.db.update_task_status(task_id, "failed", f"Video with ID {video_db_id} not found")
                return 0
            
            video_url = video_data[0]
            
            # Scrape comments
            comments = self.scraper.get_video_comments(video_url, max_comments)
            
            # Initialize content detector
            detector = VietnameseDangerousContentDetector()
            
            # Analyze all comments together
            if comments:
                comment_analysis = detector.analyze_comments(comments)
                
                # If dangerous content found in comments, store the analysis
                if comment_analysis["is_dangerous"]:
                    # Insert comment analysis as a special type of content analysis
                    analysis_id = self.db.insert("content_analysis", {
                        "transcription_id": None,  # Not associated with a transcription
                        "video_id": video_db_id,  # Directly associated with video
                        "content_type": "comments",
                        "is_dangerous": 1,
                        "highest_severity": comment_analysis["highest_severity"],
                        "analysis_results": json.dumps(comment_analysis, ensure_ascii=False)
                    })
                    
                    # Insert detected categories
                    for category in comment_analysis["dangerous_categories"]:
                        # Find the highest severity for this category across all comments
                        severity = 1
                        keywords = []
                        count = 0
                        
                        for dangerous_comment in comment_analysis["dangerous_comments"]:
                            if category in dangerous_comment["analysis"]["dangerous_categories"]:
                                cat_data = dangerous_comment["analysis"]["matches"].get(category, {})
                                severity = max(severity, cat_data.get("severity", 1))
                                if "keywords" in cat_data:
                                    keywords.extend(cat_data["keywords"])
                                count += cat_data.get("count", 0)
                        
                        # Deduplicate keywords
                        keywords = list(set(keywords))
                        
                        self.db.insert("analysis_categories", {
                            "analysis_id": analysis_id,
                            "category_name": category,
                            "severity": severity,
                            "keywords": json.dumps(keywords, ensure_ascii=False),
                            "count": count
                        })
            
            # Add comments to database
            for comment in comments:
                self.db.insert("comments", {
                    "video_id": video_db_id,
                    "author": comment["author"],
                    "comment_text": comment["text"],
                    "likes": comment["likes"],
                    "comment_date": comment["date"],
                    "is_verified": 1 if comment["is_verified"] else 0,
                    "is_pinned": 1 if comment["is_pinned"] else 0
                })
            
            self.db.update_task_status(task_id, "completed")
            return len(comments)
            
        except Exception as e:
            error_msg = f"Error scraping video comments: {e}\n{traceback.format_exc()}"
            print(error_msg)
            self.db.update_task_status(task_id, "failed", error_msg)
            return 0


class VideoProcessor:
    """Manages processing of YouTube videos (downloading, transcription, analysis)."""
    
    def __init__(self, db_path: str, output_folder: str = "downloads"):
        """
        Initialize the video processor.
        
        Args:
            db_path: Path to SQLite database file
            output_folder: Folder to store downloaded files
        """
        self.db_path = db_path
        self.db = DatabaseManager(db_path)
        self.output_folder = output_folder
        self.detector = VietnameseDangerousContentDetector()
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
    
    def close(self):
        """Close resources."""
        if self.db:
            self.db.close()
            
    def analyze_video_title(self, video_db_id: int, min_severity: int = 1) -> Dict[str, Any]:
        """
        Analyze a video title for dangerous content.
        
        Args:
            video_db_id: Database ID of the video
            min_severity: Minimum severity level for content analysis
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Get video title from database
            db = DatabaseManager(self.db_path)
            video_data = db.fetchone(
                "SELECT title FROM videos WHERE id = ?", 
                (video_db_id,)
            )
            
            if not video_data:
                return {"error": f"Video with ID {video_db_id} not found"}
            
            title = video_data[0]
            
            # Initialize content detector
            detector = VietnameseDangerousContentDetector()
            
            # Analyze the title
            title_analysis = detector.analyze_text(title, min_severity)
            title_analysis["content_type"] = "title"  # Add content type marker
            
            # If title contains dangerous content, store the analysis
            if title_analysis["is_dangerous"]:
                # Insert title analysis as a special type of content analysis
                analysis_id = db.insert("content_analysis", {
                    "transcription_id": None,  # Not associated with a transcription
                    "video_id": video_db_id,  # Directly associated with video
                    "content_type": "title",
                    "is_dangerous": 1,
                    "highest_severity": title_analysis["highest_severity"],
                    "analysis_results": json.dumps(title_analysis, ensure_ascii=False)
                })
                
                # Insert detected categories
                for category in title_analysis["dangerous_categories"]:
                    if category in title_analysis["matches"]:
                        db.insert("analysis_categories", {
                            "analysis_id": analysis_id,
                            "category_name": category,
                            "severity": title_analysis["matches"][category]["severity"],
                            "keywords": json.dumps(title_analysis["matches"][category]["keywords"], ensure_ascii=False),
                            "count": title_analysis["matches"][category]["count"]
                        })
            
            db.close()
            return title_analysis
            
        except Exception as e:
            error_msg = f"Error analyzing video title: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return {"error": str(e)}
    
    def analyze_video_comments(self, video_db_id: int, min_severity: int = 1) -> Dict[str, Any]:
        """
        Analyze comments from a YouTube video for dangerous content.
        
        Args:
            video_db_id: Database ID of the video
            min_severity: Minimum severity level for content analysis
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Get comments from database
            db = DatabaseManager(self.db_path)
            comments = db.fetchall(
                "SELECT id, author, comment_text, likes, comment_date FROM comments WHERE video_id = ?", 
                (video_db_id,)
            )
            
            if not comments:
                return {"error": f"No comments found for video with ID {video_db_id}"}
            
            # Format comments for analysis
            comment_data = []
            for comment in comments:
                comment_data.append({
                    "id": comment[0],
                    "author": comment[1],
                    "text": comment[2],
                    "likes": comment[3],
                    "date": comment[4]
                })
            
            # Initialize content detector
            detector = VietnameseDangerousContentDetector()
            
            # Analyze all comments together
            comment_analysis = {
                "is_dangerous": False,
                "highest_severity": 0,
                "dangerous_categories": [],
                "content_type": "comments",
                "total_comments": len(comment_data),
                "dangerous_comments": [],
                "dangerous_comment_count": 0
            }
            
            # Analyze each comment individually
            for i, comment in enumerate(comment_data):
                # Skip empty comments
                if not comment["text"]:
                    continue
                    
                # Analyze individual comment
                result = detector.analyze_text(comment["text"], min_severity)
                
                if result["is_dangerous"]:
                    # Add this comment to the dangerous comments list
                    dangerous_comment = {
                        "index": i,
                        "comment_data": comment,
                        "analysis": result
                    }
                    comment_analysis["dangerous_comments"].append(dangerous_comment)
                    comment_analysis["dangerous_comment_count"] += 1
                    comment_analysis["is_dangerous"] = True
                    comment_analysis["highest_severity"] = max(
                        comment_analysis["highest_severity"], 
                        result["highest_severity"]
                    )
                    
                    # Add all dangerous categories found
                    for category in result["dangerous_categories"]:
                        if category not in comment_analysis["dangerous_categories"]:
                            comment_analysis["dangerous_categories"].append(category)
            
            # If dangerous content found in comments, store the analysis
            if comment_analysis["is_dangerous"]:
                # Insert comment analysis as a special type of content analysis
                analysis_id = db.insert("content_analysis", {
                    "transcription_id": None,  # Not associated with a transcription
                    "video_id": video_db_id,  # Directly associated with video
                    "content_type": "comments",
                    "is_dangerous": 1,
                    "highest_severity": comment_analysis["highest_severity"],
                    "analysis_results": json.dumps(comment_analysis, ensure_ascii=False)
                })
                
                # Insert detected categories
                for category in comment_analysis["dangerous_categories"]:
                    # Find the highest severity for this category across all comments
                    severity = 1
                    keywords = []
                    count = 0
                    
                    for dangerous_comment in comment_analysis["dangerous_comments"]:
                        if category in dangerous_comment["analysis"]["dangerous_categories"]:
                            cat_data = dangerous_comment["analysis"]["matches"].get(category, {})
                            severity = max(severity, cat_data.get("severity", 1))
                            if "keywords" in cat_data:
                                keywords.extend(cat_data["keywords"])
                            count += cat_data.get("count", 0)
                    
                    # Deduplicate keywords
                    keywords = list(set(keywords))
                    
                    db.insert("analysis_categories", {
                        "analysis_id": analysis_id,
                        "category_name": category,
                        "severity": severity,
                        "keywords": json.dumps(keywords, ensure_ascii=False),
                        "count": count
                    })
            
            db.close()
            return comment_analysis
            
        except Exception as e:
            error_msg = f"Error analyzing video comments: {e}\n{traceback.format_exc()}"
            print(error_msg)
            return {"error": str(e)}

class PipelineManager:
    """Manages the entire YouTube analysis pipeline."""
    
    def __init__(self, db_path: str, output_folder: str = "downloads"):
        """
        Initialize the pipeline manager.
        
        Args:
            db_path: Path to the SQLite database file
            output_folder: Folder to store downloaded files
        """
        self.db_path = db_path
        self.output_folder = output_folder
        # Create separate instances for each component
        # This ensures each thread has its own database connection
        self.channel_manager = ChannelManager(db_path)
        self.video_processor = VideoProcessor(db_path, output_folder)
    
    def close(self):
        """Close all resources."""
        if self.channel_manager:
            self.channel_manager.close()
        if self.video_processor:
            self.video_processor.close()
    
    def process_channel(self, channel_input: str, max_videos: int = 5, 
                   scrape_comments: bool = True, min_severity: int = 1) -> Dict[str, Any]:
        """
        Process a YouTube channel through the entire pipeline.
        
        Args:
            channel_input: Channel name, URL, or @username
            max_videos: Maximum number of videos to process
            scrape_comments: Whether to scrape video comments
            min_severity: Minimum severity level for content analysis
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "channel_id": None,
            "videos_processed": 0,
            "videos_with_dangerous_content": 0,
            "videos_with_dangerous_titles": 0,
            "videos_with_dangerous_comments": 0,
            "highest_severity_found": 0,
            "dangerous_categories": set(),
            "errors": []
        }
        
        try:
            # Step 1: Add/update channel
            print(f"Processing channel: {channel_input}")
            channel_id = self.channel_manager.add_channel(channel_input)
            
            if not channel_id:
                results["errors"].append(f"Failed to add channel: {channel_input}")
                return results
            
            results["channel_id"] = channel_id
            
            # Step 2: Scrape videos
            print(f"Scraping up to {max_videos} videos")
            video_ids = self.channel_manager.scrape_channel_videos(channel_id, max_videos)
            
            # Step 3: Process each video
            for video_id in video_ids:
                # Create a new database connection for safety
                db = DatabaseManager(self.db_path)
                
                # Get video details
                video_data = db.fetchone(
                    "SELECT title, video_id FROM videos WHERE id = ?", 
                    (video_id,)
                )
                
                db.close()
                
                if not video_data:
                    results["errors"].append(f"Video with ID {video_id} not found in database")
                    continue
                
                video_title, yt_video_id = video_data
                print(f"Processing video: {video_title}")
                
                # Step 3b: Scrape comments if requested
                if scrape_comments:
                    print("Scraping comments")
                    self.channel_manager.scrape_video_comments(video_id)
                
                # Check for any dangerous content
                db = DatabaseManager(self.db_path)
                dangerous_content = db.fetchone(
                    "SELECT COUNT(*) FROM content_analysis WHERE video_id = ? AND is_dangerous = 1",
                    (video_id,)
                )
                
                if dangerous_content and dangerous_content[0] > 0:
                    results["videos_with_dangerous_content"] += 1
                
                db.close()
            
            results["videos_processed"] = len(video_ids)
            
            # Convert set to list for JSON serialization
            results["dangerous_categories"] = list(results["dangerous_categories"])
            
            return results
            
        except Exception as e:
            error_msg = f"Error in pipeline: {e}\n{traceback.format_exc()}"
            print(error_msg)
            results["errors"].append(error_msg)
            return results

    def process_video(self, video_url: str, scrape_comments: bool = True, 
                    min_severity: int = 1) -> Dict[str, Any]:
        """
        Process a single YouTube video through the pipeline.
        
        Args:
            video_url: URL of the YouTube video
            scrape_comments: Whether to scrape video comments
            min_severity: Minimum severity level for content analysis
            
        Returns:
            Dictionary with processing results
        """
        results = {
            "video_id": None,
            "is_dangerous": False,
            "has_dangerous_title": False,
            "has_dangerous_comments": False,
            "highest_severity": 0,
            "dangerous_categories": [],
            "errors": []
        }
        
        try:
            # Extract YouTube video ID from URL
            match = re.search(r'v=([a-zA-Z0-9_-]+)', video_url)
            if not match:
                results["errors"].append(f"Invalid YouTube URL: {video_url}")
                return results
            
            yt_video_id = match.group(1)
            
            # Create a new database connection
            db = DatabaseManager(self.db_path)
            
            # Check if video already exists in database
            existing = db.fetchone(
                "SELECT id FROM videos WHERE video_id = ?", 
                (yt_video_id,)
            )
            
            db.close()
            
            if existing:
                video_db_id = existing[0]
                print(f"Video already exists in database with ID: {video_db_id}")
            else:
                # Initialize YouTube scraper
                scraper = YouTubeChannelScraper(headless=True)
                
                try:
                    # Get video details
                    video_details = scraper.get_video_details(video_url)
                    
                    # Get channel information
                    channel_url = None
                    try:
                        # Try to navigate to the channel from the video page
                        # This is a simplified approach - in a real implementation,
                        # you would use Selenium to navigate to the channel
                        channel_url = video_details.get("channel_url")
                    except:
                        pass
                    
                    # Create a new database connection
                    db = DatabaseManager(self.db_path)
                    
                    # If we couldn't get the channel URL, create a placeholder channel
                    channel_id = None
                    if channel_url:
                        channel_info = scraper.get_channel_info(channel_url)
                        
                        # Check if channel exists in database
                        existing_channel = db.fetchone(
                            "SELECT id FROM channels WHERE channel_id = ?", 
                            (channel_info["channel_id"],)
                        )
                        
                        if existing_channel:
                            channel_id = existing_channel[0]
                        else:
                            # Insert new channel
                            channel_id = db.insert("channels", {
                                "channel_id": channel_info["channel_id"],
                                "channel_name": channel_info["channel_name"],
                                "subscribers": channel_info["subscribers"],
                                "description": channel_info["description"],
                                "url": channel_info["url"]
                            })
                    else:
                        # Create a placeholder channel
                        channel_id = db.insert("channels", {
                            "channel_id": "unknown",
                            "channel_name": "Unknown Channel",
                            "subscribers": "Unknown",
                            "description": "Automatically created for video processing",
                            "url": "#"
                        })
                    
                    # Insert video
                    video_db_id = db.insert("videos", {
                        "video_id": yt_video_id,
                        "channel_id": channel_id,
                        "title": video_details["title"],
                        "url": video_url,
                        "views": video_details.get("views", "Unknown"),
                        "upload_date": video_details.get("upload_date", "Unknown"),
                        "likes": video_details.get("likes", 0),
                        "description": video_details.get("description", ""),
                        "thumbnail": video_details.get("thumbnail", "")
                    })
                    
                    db.close()
                    
                finally:
                    if scraper:
                        scraper.close()
            
            results["video_id"] = video_db_id
            
            # Step 1: Analyze video title
            print("Analyzing video title")
            self.video_processor.analyze_video_title(video_db_id, min_severity)
            
            # Step 2: Scrape comments if requested
            if scrape_comments:
                print("Scraping comments")
                self.channel_manager.scrape_video_comments(video_db_id)
            
            return results
            
        except Exception as e:
            error_msg = f"Error processing video: {e}\n{traceback.format_exc()}"
            print(error_msg)
            results["errors"].append(error_msg)
            return results