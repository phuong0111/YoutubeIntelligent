#!/usr/bin/env python3
"""
YouTube Channel Scraper

This script scrapes data from a YouTube channel using Selenium with headless Chrome.
It extracts channel information and video data based on the channel name.
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class YouTubeChannelScraper:
    """Scraper for YouTube channels using Selenium with headless Chrome."""

    def __init__(self, headless: bool = True, scroll_pause_time: float = 1.5):
        """
        Initialize the YouTube scraper.

        Args:
            headless: Whether to run Chrome in headless mode (default: True)
            scroll_pause_time: Time to pause between scrolls in seconds (default: 1.5)
        """
        self.scroll_pause_time = scroll_pause_time
        self.driver = self._setup_driver(headless)
        self.wait = WebDriverWait(self.driver, 10)

    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """
        Set up and configure the Chrome WebDriver.

        Args:
            headless: Whether to run Chrome in headless mode

        Returns:
            Configured Chrome WebDriver instance
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")

        return webdriver.Chrome(options=chrome_options)

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()

    def search_channel(self, channel_input: str) -> Optional[str]:
        """
        Search for a YouTube channel and return its URL.
        Can handle channel names, full URLs, or @username formats.

        Args:
            channel_input: Name of the channel, URL, or @username

        Returns:
            URL of the channel if found, None otherwise
        """
        # Check if input is already a YouTube URL
        if channel_input.startswith(("https://www.youtube.com/", "https://youtube.com/")):
            # Direct URL provided (either channel, user, or @username format)
            print(f"Using provided YouTube URL: {channel_input}")
            return channel_input
            
        # Check if input is a @username format without the full URL
        if channel_input.startswith("@"):
            full_url = f"https://www.youtube.com/{channel_input}"
            print(f"Converting @username to URL: {full_url}")
            return full_url
            
        # Otherwise search for the channel on YouTube
        try:
            search_url = f"https://www.youtube.com/results?search_query={channel_input.replace(' ', '+')}&sp=EgIQAg%253D%253D"  # Filter for channels
            self.driver.get(search_url)
            time.sleep(2)  # Wait for results to load

            # Find channel in search results
            channel_items = self.wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "ytd-channel-renderer")
            ))

            if not channel_items:
                print(f"No channels found for '{channel_input}'")
                return None

            # Click on the first channel in results
            channel_link = channel_items[0].find_element(By.CSS_SELECTOR, "a#main-link")
            channel_url = channel_link.get_attribute("href")
            
            return channel_url
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error searching for channel: {e}")
            return None

    def get_channel_info(self, channel_url: str) -> Dict[str, Any]:
        """
        Extract information from a YouTube channel.

        Args:
            channel_url: URL of the YouTube channel

        Returns:
            Dictionary containing channel information
        """
        try:
            # Navigate to the channel page
            self.driver.get(channel_url)
            time.sleep(3)  # Wait for page to load

            # Extract channel name
            channel_name = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "ytd-channel-name yt-formatted-string#text")
            )).text

            # Extract subscriber count
            try:
                subscribers_text = self.driver.find_element(
                    By.XPATH, "//span[contains(text(), 'subscribers')]"
                ).text
            except NoSuchElementException:
                subscribers_text = "Hidden"

            # Extract channel thumbnail/avatar
            try:
                # Try to find the avatar using the specific classes from the HTML you provided
                thumbnail_element = self.driver.find_element(
                    By.CSS_SELECTOR, "img.yt-core-image.yt-spec-avatar-shape__image"
                )
                thumbnail = thumbnail_element.get_attribute("src")
                
                # If we can't find it with the specific class, fall back to more generic selectors
                if not thumbnail:
                    thumbnail_element = self.driver.find_element(
                        By.CSS_SELECTOR, "#avatar img, #channel-header-container img, #img"
                    )
                    thumbnail = thumbnail_element.get_attribute("src")
            except NoSuchElementException:
                thumbnail = None

            # Extract channel description
            try:
                about_tab_url = f"{channel_url}/about"
                self.driver.get(about_tab_url)
                time.sleep(2)
                description = self.driver.find_element(
                    By.CSS_SELECTOR, "ytd-channel-about-metadata-renderer #description-container"
                ).text
            except NoSuchElementException:
                description = "No description available"

            # Extract channel ID or handle from URL
            channel_id_match = re.search(r"channel/(UC[\w-]+)", channel_url)
            username_match = re.search(r"@([\w-]+)", channel_url)
            
            if channel_id_match:
                channel_id = channel_id_match.group(1)
            elif username_match:
                channel_id = f"@{username_match.group(1)}"
            else:
                channel_id = "Unknown"

            # Navigate back to videos tab
            videos_url = f"{channel_url}/videos"
            self.driver.get(videos_url)
            time.sleep(2)

            return {
                "channel_name": channel_name,
                "channel_id": channel_id,
                "subscribers": subscribers_text,
                "description": description,
                "url": channel_url,
                "thumbnail": thumbnail
            }
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error getting channel info: {e}")
            return {
                "channel_name": "Unknown",
                "channel_id": "Unknown",
                "subscribers": "Unknown",
                "description": "Failed to retrieve",
                "url": channel_url,
                "thumbnail": None
            }

    def get_channel_videos(self, channel_url: str, max_videos: int = 20) -> List[Dict[str, Any]]:
        """
        Extract video information from a YouTube channel.

        Args:
            channel_url: URL of the YouTube channel
            max_videos: Maximum number of videos to extract (default: 20)

        Returns:
            List of dictionaries containing video information
        """
        videos = []
        try:
            # Navigate to the videos tab
            videos_url = f"{channel_url}/videos"
            self.driver.get(videos_url)
            time.sleep(3)  # Wait for page to load

            # Scroll down to load more videos
            last_height = self.driver.execute_script("return document.documentElement.scrollHeight")
            
            while len(videos) < max_videos:
                # Scroll down
                self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
                time.sleep(self.scroll_pause_time)
                
                # Get all video elements
                video_elements = self.driver.find_elements(By.CSS_SELECTOR, "ytd-rich-item-renderer")
                
                # Process videos we haven't processed yet
                for element in video_elements[len(videos):]:
                    if len(videos) >= max_videos:
                        break
                    
                    try:
                        # Extract video title
                        title = element.find_element(By.CSS_SELECTOR, "#video-title").text
                        
                        # Extract video URL
                        video_url = element.find_element(By.CSS_SELECTOR, "#video-title-link").get_attribute("href")
                        
                        # Extract video ID from URL
                        video_id = re.search(r"v=([\w-]+)", video_url).group(1) if video_url else "Unknown"
                        
                        # Extract view count
                        metadata_line = element.find_element(By.CSS_SELECTOR, "#metadata-line").text.split('\n')
                        views = metadata_line[0] if len(metadata_line) > 0 else "Unknown"
                        
                        
                        # Extract upload date
                        upload_date = metadata_line[1] if len(metadata_line) > 1 else "Unknown"
                        
                        # Extract thumbnail URL
                        thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                        
                        videos.append({
                            "title": title,
                            "video_id": video_id,
                            "url": video_url,
                            "views": views,
                            "upload_date": upload_date,
                            "thumbnail": thumbnail
                        })
                    except (NoSuchElementException, AttributeError) as e:
                        print(f"Error extracting video info: {e}")
                        continue
                
                # Check if we've reached the end of the page
                new_height = self.driver.execute_script("return document.documentElement.scrollHeight")
                if new_height == last_height or len(videos) >= max_videos:
                    break
                last_height = new_height

            return videos[:max_videos]
        
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error getting videos: {e}")
            return videos

    def get_video_details(self, video_url: str) -> Dict[str, Any]:
        """
        Extract detailed information from a YouTube video.

        Args:
            video_url: URL of the YouTube video

        Returns:
            Dictionary containing video details
        """
        try:
            self.driver.get(video_url)
            time.sleep(3)  # Wait for video page to load
            
            # Wait for title to be visible
            title = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "h1.ytd-watch-metadata yt-formatted-string")
            )).text
            
            # Extract view count
            try:
                view_count = self.driver.find_element(
                    By.CSS_SELECTOR, ".view-count"
                ).text
            except NoSuchElementException:
                view_count = "Unknown"
            
            # Extract like count
            try:
                like_count = self.driver.find_element(
                    By.CSS_SELECTOR, "#vote-count-middle"
                ).text.strip()
                like_count = int(like_count) if like_count != "" else 0
            except NoSuchElementException:
                like_count = 0
            
            # Extract upload date
            try:
                upload_date = self.driver.find_element(
                    By.CSS_SELECTOR, "ytd-watch-metadata #info-strings yt-formatted-string"
                ).text
            except NoSuchElementException:
                upload_date = "Unknown"
            
            # Extract description
            try:
                # Click show more if available
                try:
                    show_more = self.driver.find_element(By.CSS_SELECTOR, "#description-inline-expander tp-yt-paper-button#expand")
                    show_more.click()
                    time.sleep(1)
                except NoSuchElementException:
                    pass
                
                description = self.driver.find_element(
                    By.CSS_SELECTOR, "#description-inline-expander #content"
                ).text
            except NoSuchElementException:
                description = "No description available"
            
            # Extract video ID from URL
            video_id = re.search(r"v=([\w-]+)", video_url)
            video_id = video_id.group(1) if video_id else "Unknown"
            
            return {
                "title": title,
                "video_id": video_id,
                "url": video_url,
                "views": view_count,
                "likes": like_count,
                "upload_date": upload_date,
                "description": description,
                "thumbnail": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
            }
            
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Error getting video details: {e}")
            return {
                "title": "Unknown",
                "video_id": "Unknown",
                "url": video_url,
                "views": "Unknown",
                "likes": "Unknown",
                "upload_date": "Unknown",
                "description": "Failed to retrieve",
                "thumbnail": "Unknown"
            }

    def analyze_channel(self, channel_name: str, max_videos: int = 20) -> Dict[str, Any]:
        """
        Analyze a YouTube channel based on name.

        Args:
            channel_name: Name of the channel to analyze
            max_videos: Maximum number of videos to analyze

        Returns:
            Dictionary containing channel analysis
        """
        result = {
            "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "channel_name_query": channel_name,
            "channel_info": {},
            "videos": [],
            "analysis": {}
        }
        
        try:
            # Search for the channel
            print(f"Searching for channel: {channel_name}")
            channel_url = self.search_channel(channel_name)
            
            if not channel_url:
                result["error"] = f"Could not find channel: {channel_name}"
                return result
            
            # Get channel information
            print(f"Found channel: {channel_url}")
            print("Gathering channel information...")
            result["channel_info"] = self.get_channel_info(channel_url)
            
            # Get videos from the channel
            print(f"Gathering up to {max_videos} videos...")
            result["videos"] = self.get_channel_videos(channel_url, max_videos)
            
            # Analyze the first video in detail
            if result["videos"]:
                print("Analyzing latest video in detail...")
                latest_video = result["videos"][0]
                result["latest_video_details"] = self.get_video_details(latest_video["url"])
            
            # Perform basic channel analysis
            if result["videos"]:
                print("Performing channel analysis...")
                result["analysis"] = self._perform_analysis(result["videos"])
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            print(f"Error analyzing channel: {e}")
            return result

    def _perform_analysis(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform basic analysis on channel videos.
        
        Args:
            videos: List of video information dictionaries
            
        Returns:
            Dictionary containing analysis results
        """
        if not videos:
            return {"error": "No videos to analyze"}
        
        # Extract view counts where possible and convert to numbers
        view_counts = []
        for video in videos:
            try:
                # Handle formats like "1.2M views" or "4K views"
                views_text = video.get("views", "0 views").split(" ")[0].lower()
                
                if 'k' in views_text:
                    views = float(views_text.replace('k', '')) * 1000
                elif 'm' in views_text:
                    views = float(views_text.replace('m', '')) * 1000000
                elif 'b' in views_text:
                    views = float(views_text.replace('b', '')) * 1000000000
                else:
                    views = float(views_text.replace(',', ''))
                
                view_counts.append(views)
            except (ValueError, IndexError):
                continue
        
        # Calculate statistics
        analysis = {}
        if view_counts:
            analysis["total_videos_analyzed"] = len(videos)
            analysis["average_views"] = sum(view_counts) / len(view_counts)
            analysis["max_views"] = max(view_counts)
            analysis["min_views"] = min(view_counts)
            
            # Find most popular video
            max_views_index = view_counts.index(max(view_counts))
            analysis["most_popular_video"] = {
                "title": videos[max_views_index].get("title", "Unknown"),
                "url": videos[max_views_index].get("url", "Unknown"),
                "views": videos[max_views_index].get("views", "Unknown")
            }
            
            # Analyze common words in titles
            title_words = []
            for video in videos:
                title = video.get("title", "").lower()
                # Remove common words and punctuation
                for word in re.findall(r'\b[a-z]+\b', title):
                    if len(word) > 3 and word not in ["this", "that", "with", "from", "what", "when", "where", "which", "your"]:
                        title_words.append(word)
            
            # Count word frequencies
            word_counts = {}
            for word in title_words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # Get top words
            sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
            analysis["common_title_words"] = [{"word": word, "count": count} for word, count in sorted_words[:5]]
        
        return analysis
    
    def get_video_comments(self, video_url: str, max_comments: int = 20) -> List[Dict[str, Any]]:
        """
        Extract comments from a YouTube video.

        Args:
            video_url: URL of the YouTube video
            max_comments: Maximum number of comments to extract (default: 20)

        Returns:
            List of dictionaries containing comment information
        """
        comments = []
        try:
            # Navigate to the video page
            self.driver.get(video_url)
            time.sleep(3)  # Wait for video page to load
            
            # Scroll down to load comments section
            self.driver.execute_script("window.scrollTo(0, window.scrollY + 500);")
            time.sleep(2)
            
            # Wait for comments to be visible
            try:
                self.wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ytd-comments#comments")
                ))
            except TimeoutException:
                print("Comments section not found or disabled for this video")
                return comments
            
            # Scroll down to load more comments
            last_comment_count = 0
            
            # Keep scrolling until we have enough comments or no new comments are loading
            while len(comments) < max_comments:
                # Find all comment elements
                comment_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, "ytd-comment-thread-renderer"
                )
                
                # If no new comments have loaded, break the loop
                if len(comment_elements) == last_comment_count:
                    break
                
                last_comment_count = len(comment_elements)
                
                # Process comments we haven't processed yet
                for element in comment_elements[len(comments):]:
                    if len(comments) >= max_comments:
                        break
                    
                    try:
                        # Extract author name
                        author_element = element.find_element(
                            By.CSS_SELECTOR, "#author-text"
                        )
                        author_name = author_element.text.strip()
                        
                        # Extract comment text
                        comment_text_element = element.find_element(
                            By.CSS_SELECTOR, "#content-text"
                        )
                        comment_text = comment_text_element.text.strip()
                        
                        # Extract likes count
                        try:
                            likes_element = element.find_element(
                                By.CSS_SELECTOR, "#vote-count-middle"
                            )
                            likes_count = likes_element.text.strip()
                            # Convert text like "5.2K" to numeric value if needed
                            if not likes_count:
                                likes_count = "0"
                        except NoSuchElementException:
                            likes_count = "0"
                        
                        # Extract comment date
                        try:
                            date_element = element.find_element(
                                By.CSS_SELECTOR, "#published-time-text a"
                            )
                            comment_date = date_element.text.strip()
                        except NoSuchElementException:
                            comment_date = "Unknown"
                        
                        # Check if there's a verified badge
                        is_verified = False
                        try:
                            element.find_element(By.CSS_SELECTOR, "#author-comment-badge")
                            is_verified = True
                        except NoSuchElementException:
                            pass
                        
                        # Check if this is a pinned comment
                        is_pinned = False
                        try:
                            element.find_element(By.CSS_SELECTOR, "#pinned-comment-badge")
                            is_pinned = True
                        except NoSuchElementException:
                            pass
                        
                        comments.append({
                            "author": author_name,
                            "text": comment_text,
                            "likes": likes_count,
                            "date": comment_date,
                            "is_verified": is_verified,
                            "is_pinned": is_pinned
                        })
                        
                    except (NoSuchElementException, StaleElementReferenceException) as e:
                        print(f"Error extracting comment: {e}")
                        continue
                
                # Scroll down to load more comments
                self.driver.execute_script(
                    "window.scrollTo(0, document.documentElement.scrollHeight);"
                )
                time.sleep(self.scroll_pause_time)
                
                # If we've collected enough comments, break the loop
                if len(comments) >= max_comments:
                    break
            
            return comments[:max_comments]
            
        except Exception as e:
            print(f"Error getting comments: {e}")
            return comments

def save_to_json(data: Dict[str, Any], filename: str):
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filename: Name of the file to save to
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to {filename}")


def main():
    import argparse
    """Main function to run the YouTube channel scraper."""
    parser = argparse.ArgumentParser(description='Scrape YouTube channel information')
    parser.add_argument('channel_input', type=str, 
                       help='YouTube channel name, URL, or @username (e.g., "Channel Name", "https://youtube.com/c/ChannelName", or "@username")')
    parser.add_argument('--videos', type=int, default=20, help='Maximum number of videos to scrape (default: 20)')
    parser.add_argument('--output', type=str, default=None, help='Output JSON filename (default: channel_name.json)')
    parser.add_argument('--visible', action='store_true', help='Run Chrome in visible mode (default: headless)')
    parser.add_argument('--comments', action='store_true', help='Scrape comments from the latest video (default: False)')
    parser.add_argument('--max-comments', type=int, default=20, help='Maximum number of comments to scrape (default: 20)')
    parser.add_argument('--detailed', action='store_true', help='Perform detailed analysis on all videos (default: latest video only)')
    
    args = parser.parse_args()
    
    # Generate sanitized output filename
    if '@' in args.channel_input:
        # For @username format
        sanitized_name = args.channel_input.strip('@').replace(' ', '_')
    elif '/' in args.channel_input:
        # For URLs, extract the last part
        sanitized_name = args.channel_input.rstrip('/').split('/')[-1].replace(' ', '_')
    else:
        # For regular channel names
        sanitized_name = args.channel_input.replace(' ', '_')
        
    output_file = args.output or f"{sanitized_name}_analysis.json"
    
    scraper = YouTubeChannelScraper(headless=not args.visible)
    
    try:
        print(f"Starting analysis of YouTube channel: {args.channel_input}")
        
        # Search for the channel
        channel_url = scraper.search_channel(args.channel_input)
        
        if not channel_url:
            print(f"Error: Could not find channel: {args.channel_input}")
            return
        
        # Initialize the result dictionary
        result = {
            "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "channel_name_query": args.channel_input,
            "channel_info": {},
            "videos": [],
            "analysis": {}
        }
        
        # Get channel information
        print(f"Found channel: {channel_url}")
        print("Gathering channel information...")
        result["channel_info"] = scraper.get_channel_info(channel_url)
        
        # Get videos from the channel
        print(f"Gathering up to {args.videos} videos...")
        result["videos"] = scraper.get_channel_videos(channel_url, args.videos)
        
        # Analyze videos
        if result["videos"]:
            # Analyze latest video in detail by default
            print("Analyzing latest video in detail...")
            latest_video = result["videos"][1]
            result["latest_video_details"] = scraper.get_video_details(latest_video["url"])
            
            # If requested, collect comments from the latest video
            if args.comments and latest_video.get("url"):
                print(f"Collecting up to {args.max_comments} comments from latest video...")
                result["latest_video_comments"] = scraper.get_video_comments(
                    latest_video["url"], max_comments=args.max_comments
                )
            
            # If detailed analysis is requested, analyze all videos
            if args.detailed:
                print("Performing detailed analysis on all videos...")
                result["video_details"] = []
                for i, video in enumerate(result["videos"]):
                    print(f"Analyzing video {i+1}/{len(result['videos'])}: {video.get('title', 'Unknown')}")
                    video_details = scraper.get_video_details(video["url"])
                    result["video_details"].append(video_details)
                    
                    # If comments are requested, get them for all videos
                    if args.comments:
                        print(f"Collecting comments for video {i+1}...")
                        video_details["comments"] = scraper.get_video_comments(
                            video["url"], max_comments=args.max_comments
                        )
                    
                    # Pause between videos to avoid rate limiting
                    if i < len(result["videos"]) - 1:
                        time.sleep(1)
            
            # Perform channel analysis
            print("Performing channel analysis...")
            result["analysis"] = scraper._perform_analysis(result["videos"])
        
        # Print summary
        channel_name = result.get("channel_info", {}).get("channel_name", args.channel_input)
        print(f"Analysis complete for {channel_name}")
        print(f"Found {len(result.get('videos', []))} videos")
        
        if args.comments:
            comments_count = len(result.get("latest_video_comments", []))
            print(f"Collected {comments_count} comments from latest video")
        
        # Save results to JSON
        save_to_json(result, output_file)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    main()