#!/usr/bin/env python3
# integration_test.py - Test the entire YouTube analysis pipeline

import requests
import time
import json
import argparse
import sys

# Configuration
API_GATEWAY_URL = "http://localhost:5005"  # Change if your API gateway is on a different host/port

def test_health_check():
    """Test health check endpoint to ensure all services are running."""
    print("Testing system health...")
    
    try:
        response = requests.get(f"{API_GATEWAY_URL}/api/health")
        if response.status_code != 200:
            print(f"ERROR: Health check failed with status code {response.status_code}")
            return False
            
        health_data = response.json()
        services_status = health_data.get("services", {})
        
        all_services_up = True
        for service, status in services_status.items():
            if status != "up":
                all_services_up = False
                print(f"WARNING: Service '{service}' is down")
        
        if all_services_up:
            print("All services are up and running!")
        else:
            print("Some services are down. The test may not complete successfully.")
        
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Could not connect to API Gateway at {API_GATEWAY_URL}")
        return False
    except Exception as e:
        print(f"ERROR during health check: {str(e)}")
        return False

def wait_for_task_completion(service_type, task_id, timeout=300):
    """Wait for a task to complete with a timeout."""
    print(f"Waiting for {service_type} task {task_id} to complete...")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{API_GATEWAY_URL}/api/task/{service_type}/{task_id}")
            if response.status_code != 200:
                print(f"WARNING: Error checking task status: {response.status_code}")
                time.sleep(5)
                continue
                
            task_data = response.json()
            task = task_data.get("task", {})
            status = task.get("status")
            
            if status == "completed":
                print(f"Task {task_id} completed successfully!")
                return task.get("result", {})
            elif status == "failed":
                error = task.get("error", "Unknown error")
                print(f"ERROR: Task {task_id} failed: {error}")
                return None
            
            # Still in progress
            print(f"Task status: {status}. Waiting...")
            time.sleep(10)
            
        except Exception as e:
            print(f"ERROR checking task status: {str(e)}")
            time.sleep(5)
    
    print(f"ERROR: Timeout waiting for task {task_id} to complete")
    return None

def process_channel(channel_input):
    """Process a YouTube channel through the entire pipeline."""
    print(f"\n=== Processing channel: {channel_input} ===\n")
    
    # Step 1: Start channel scraping
    print("Step 1: Initiating channel scraping...")
    try:
        response = requests.post(
            f"{API_GATEWAY_URL}/api/scrape/channel",
            json={"channel_input": channel_input}
        )
        
        if response.status_code != 200:
            print(f"ERROR: Failed to initiate channel scraping: {response.status_code}")
            return False
            
        data = response.json()
        scrape_task_id = data.get("task_id")
        
        if not scrape_task_id:
            print("ERROR: No task ID returned from scraping request")
            return False
            
        print(f"Channel scraping initiated with task ID: {scrape_task_id}")
        
        # Wait for channel scraping to complete
        result = wait_for_task_completion("scrape", scrape_task_id)
        if not result:
            print("ERROR: Channel scraping failed")
            return False
            
        channel_id = result.get("channel_id")
        if not channel_id:
            print("ERROR: No channel ID found in scraping result")
            return False
            
        print(f"Channel scraping completed. Channel ID in database: {channel_id}")
        
        # Step 2: Get channel details and video list
        print("\nStep 2: Getting channel details...")
        response = requests.get(f"{API_GATEWAY_URL}/api/channels/{channel_id}")
        
        if response.status_code != 200:
            print(f"ERROR: Failed to get channel details: {response.status_code}")
            return False
            
        channel_data = response.json().get("channel", {})
        channel_name = channel_data.get("name", "Unknown Channel")
        videos = channel_data.get("videos", [])
        
        print(f"Channel name: {channel_name}")
        print(f"Total videos found: {len(videos)}")
        
        if not videos:
            print("ERROR: No videos found for this channel")
            
            # Step 2.1: Try explicitly scraping videos
            print("Explicitly requesting video scraping...")
            response = requests.post(
                f"{API_GATEWAY_URL}/api/scrape/videos",
                json={"channel_id": channel_id, "max_videos": 3}
            )
            
            if response.status_code != 200:
                print(f"ERROR: Failed to initiate video scraping: {response.status_code}")
                return False
                
            video_scrape_task_id = response.json().get("task_id")
            result = wait_for_task_completion("scrape", video_scrape_task_id)
            
            if not result:
                print("ERROR: Video scraping failed")
                return False
                
            # Get updated channel details
            response = requests.get(f"{API_GATEWAY_URL}/api/channels/{channel_id}")
            
            if response.status_code != 200:
                print(f"ERROR: Failed to get updated channel details: {response.status_code}")
                return False
                
            channel_data = response.json().get("channel", {})
            videos = channel_data.get("videos", [])
            print(f"After explicit scraping - videos found: {len(videos)}")
            
        # Limit to max 3 videos for the test
        videos_to_process = videos[:3]
        
        # Step 3: Process each video
        print(f"\nStep 3: Processing {len(videos_to_process)} videos...")
        
        for idx, video in enumerate(videos_to_process):
            video_id = video.get("id")
            video_title = video.get("title", "Unknown Title")
            
            print(f"\nProcessing video {idx+1}/{len(videos_to_process)}: {video_title}")
            
            # Step 3.1: Process the video
            response = requests.post(
                f"{API_GATEWAY_URL}/api/process/video",
                json={"video_url": f"https://www.youtube.com/watch?v={video.get('video_id')}", "scrape_comments": True}
            )
            
            if response.status_code != 200:
                print(f"ERROR: Failed to process video: {response.status_code}")
                continue
                
            process_data = response.json()
            download_task_id = process_data.get("download_task_id")
            
            if not download_task_id:
                print("ERROR: No download task ID returned")
                continue
                
            # Wait for download to complete
            print("Waiting for video download to complete...")
            result = wait_for_task_completion("download", download_task_id)
            
            if not result:
                print(f"ERROR: Download failed for video {video_id}")
                continue
                
            # Step 3.2: Get video details and check if transcription completed automatically
            print("Checking video processing status...")
            response = requests.get(f"{API_GATEWAY_URL}/api/videos/{video_id}")
            
            if response.status_code != 200:
                print(f"ERROR: Failed to get video details: {response.status_code}")
                continue
                
            video_data = response.json().get("video", {})
            processing_status = video_data.get("processing_status", {})
            
            if not processing_status.get("transcribed", False):
                # Step 3.3: Manually trigger transcription if needed
                print("Transcription not completed automatically. Triggering manually...")
                response = requests.post(f"{API_GATEWAY_URL}/api/videos/{video_id}/transcribe")
                
                if response.status_code != 200:
                    print(f"ERROR: Failed to trigger transcription: {response.status_code}")
                    continue
                    
                # Get the transcription tasks and wait for them
                tasks = response.json().get("tasks", [])
                for task_info in tasks:
                    if "task_id" in task_info:
                        wait_for_task_completion("transcribe", task_info["task_id"])
            
            # Step 3.4: Get updated video details and check if analysis is needed
            response = requests.get(f"{API_GATEWAY_URL}/api/videos/{video_id}")
            
            if response.status_code != 200:
                print(f"ERROR: Failed to get updated video details: {response.status_code}")
                continue
                
            video_data = response.json().get("video", {})
            processing_status = video_data.get("processing_status", {})
            transcriptions = video_data.get("transcriptions", [])
            
            if not processing_status.get("analyzed", False) and transcriptions:
                # Step 3.5: Manually trigger analysis for each transcription
                print("Analysis not completed automatically. Triggering manually...")
                
                for transcription in transcriptions:
                    transcription_id = transcription.get("id")
                    if not transcription_id:
                        continue
                        
                    if not transcription.get("analysis"):
                        print(f"Triggering analysis for transcription {transcription_id}...")
                        response = requests.post(
                            f"{API_GATEWAY_URL}/api/transcriptions/{transcription_id}/analyze",
                            json={"min_severity": 1}
                        )
                        
                        if response.status_code != 200:
                            print(f"ERROR: Failed to trigger analysis: {response.status_code}")
                            continue
                            
                        task_id = response.json().get("task_id")
                        if task_id:
                            wait_for_task_completion("transcribe", task_id)  # Analysis tasks use the transcribe service
            
            # Step 3.6: Scrape comments if not already done
            if not video_data.get("comments"):
                print("Scraping comments...")
                response = requests.post(
                    f"{API_GATEWAY_URL}/api/scrape/comments",
                    json={"video_id": video_id, "max_comments": 20}
                )
                
                if response.status_code != 200:
                    print(f"ERROR: Failed to scrape comments: {response.status_code}")
                    continue
                    
                scrape_task_id = response.json().get("task_id")
                if scrape_task_id:
                    wait_for_task_completion("scrape", scrape_task_id)
            
            # Step 3.7: Final check of video processing
            response = requests.get(f"{API_GATEWAY_URL}/api/videos/{video_id}")
            
            if response.status_code != 200:
                print(f"ERROR: Failed to get final video details: {response.status_code}")
                continue
                
            video_data = response.json().get("video", {})
            processing_status = video_data.get("processing_status", {})
            comments_count = len(video_data.get("comments", []))
            
            print(f"\nVideo processing completed: {video_data.get('title')}")
            print(f"Processing status: {json.dumps(processing_status)}")
            print(f"Comments scraped: {comments_count}")
            
            # Print analysis results if available
            for transcription in video_data.get("transcriptions", []):
                if transcription.get("analysis"):
                    analysis = transcription.get("analysis")
                    print("\nContent Analysis Results:")
                    print(f"Dangerous content detected: {'Yes' if analysis.get('is_dangerous') else 'No'}")
                    print(f"Highest severity level: {analysis.get('highest_severity')}")
                    
                    if analysis.get("categories"):
                        print("\nDetected categories:")
                        for category in analysis.get("categories"):
                            print(f"- {category.get('name')} (Severity: {category.get('severity')})")
                            print(f"  Keywords: {', '.join(category.get('keywords', []))}")
                            print(f"  Count: {category.get('count')}")
        
        print("\n=== Channel processing completed successfully ===")
        return True
        
    except Exception as e:
        print(f"ERROR during channel processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='YouTube Analysis System Integration Test')
    parser.add_argument('channel', help='YouTube channel ID, username, or URL to process')
    parser.add_argument('--api-url', help='API Gateway URL', default='http://localhost:5005')
    
    args = parser.parse_args()
    
    global API_GATEWAY_URL
    API_GATEWAY_URL = args.api_url
    
    # Check if services are running
    if not test_health_check():
        print("ERROR: System health check failed. Please ensure all services are running.")
        sys.exit(1)
    
    # Process the channel
    success = process_channel(args.channel)
    
    if success:
        print("\nIntegration test completed successfully!")
        sys.exit(0)
    else:
        print("\nIntegration test failed. See errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()