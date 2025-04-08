# import os
# import json
# import argparse
# from typing import Dict, Any, List, Optional
# from flask import Flask, request, jsonify, Response
# from flask_cors import CORS
# import threading
# import uuid
# import time
# from datetime import datetime
# import queue
# import traceback

# # Import our pipeline components
# from db.db_setup import DatabaseManager, create_schema_file
# from modules.core_modules import PipelineManager

# # Initialize Flask app
# app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes

# # Global variables
# pipeline_manager = None
# db_path = None
# output_folder = None
# active_tasks = {}
# task_results = {}
# task_queue = queue.Queue()
# worker_thread = None
# running = True

# def worker_function():
#     """Worker thread that processes tasks from the queue."""
#     global running, pipeline_manager, db_path, output_folder
    
#     while running:
#         try:
#             # Get task from queue with timeout
#             try:
#                 task = task_queue.get(timeout=1.0)
#             except queue.Empty:
#                 continue
            
#             task_id = task["id"]
#             task_type = task["type"]
            
#             # Create a new pipeline manager for this task
#             # This ensures each task has its own database connection
#             task_pipeline = PipelineManager(db_path, output_folder)
            
#             try:
#                 if task_type == "channel":
#                     active_tasks[task_id]["status"] = "in_progress"
                    
#                     # Process channel
#                     channel_input = task["params"]["channel_input"]
#                     max_videos = task["params"]["max_videos"]
#                     scrape_comments = task["params"]["scrape_comments"]
#                     min_severity = task["params"]["min_severity"]
                    
#                     results = task_pipeline.process_channel(
#                         channel_input, max_videos, scrape_comments, min_severity
#                     )
                    
#                     active_tasks[task_id]["status"] = "completed"
#                     active_tasks[task_id]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     task_results[task_id] = results
                
#                 elif task_type == "video":
#                     active_tasks[task_id]["status"] = "in_progress"
                    
#                     # Process video
#                     video_url = task["params"]["video_url"]
#                     scrape_comments = task["params"]["scrape_comments"]
#                     min_severity = task["params"]["min_severity"]
                    
#                     results = task_pipeline.process_video(
#                         video_url, scrape_comments, min_severity
#                     )
                    
#                     active_tasks[task_id]["status"] = "completed"
#                     active_tasks[task_id]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                     task_results[task_id] = results
            
#             except Exception as e:
#                 error_msg = f"Error processing task: {e}\n{traceback.format_exc()}"
#                 print(error_msg)
#                 active_tasks[task_id]["status"] = "failed"
#                 active_tasks[task_id]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#                 active_tasks[task_id]["error"] = str(e)
#                 task_results[task_id] = {"errors": [str(e)]}
            
#             finally:
#                 # Clean up resources
#                 if task_pipeline:
#                     task_pipeline.close()
                
#                 # Mark task as done
#                 task_queue.task_done()
        
#         except Exception as e:
#             print(f"Error in worker thread: {e}")
#             time.sleep(1)  # Prevent tight loop in case of repeated errors

# def initialize_server(db_file_path: str, output_dir: str, schema_path: str) -> None:
#     """
#     Initialize the server components.
    
#     Args:
#         db_file_path: Path to the SQLite database file
#         output_dir: Folder to store downloaded files
#         schema_path: Path to the database schema file
#     """
#     global pipeline_manager, db_path, output_folder, worker_thread
    
#     # Save paths for worker threads
#     db_path = db_file_path
#     output_folder = output_dir
    
#     # Ensure output folder exists
#     os.makedirs(output_folder, exist_ok=True)
    
#     # Create database schema file if it doesn't exist
#     if not os.path.exists(schema_path):
#         with open('db/schema.sql', 'r') as f:
#             schema_content = f.read()
#         create_schema_file(schema_content, schema_path)
    
#     # Initialize pipeline manager for API requests that don't require a worker thread
#     pipeline_manager = PipelineManager(db_path, output_folder)
    
#     # Start worker thread
#     worker_thread = threading.Thread(target=worker_function)
#     worker_thread.daemon = True
#     worker_thread.start()
    
#     print(f"Server initialized with database at {db_path} and output folder at {output_folder}")


# # API Routes

# @app.route('/api/health', methods=['GET'])
# def health_check() -> Response:
#     """Health check endpoint."""
#     return jsonify({
#         "status": "ok",
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "active_tasks": len(active_tasks),
#         "queued_tasks": task_queue.qsize()
#     })


# @app.route('/api/channels', methods=['GET'])
# def get_channels() -> Response:
#     """Get list of channels."""
#     try:
#         # Create a new database manager for this request
#         db = DatabaseManager(db_path)
        
#         channels = db.fetchall(
#             "SELECT id, channel_id, channel_name, subscribers, url, scrape_time, thumbnail FROM channels ORDER BY scrape_time DESC"
#         )
        
#         return jsonify({
#             "status": "success",
#             "channels": [
#                 {
#                     "id": c[0],
#                     "channel_id": c[1],
#                     "name": c[2],
#                     "subscribers": c[3],
#                     "url": c[4],
#                     "scrape_time": c[5],
#                     "thumbnail": c[6]
#                 } 
#                 for c in channels
#             ]
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#     finally:
#         if db:
#             db.close()


# @app.route('/api/channels/<int:channel_id>', methods=['GET'])
# def get_channel(channel_id: int) -> Response:
#     """Get channel details."""
#     try:
#         # Create a new database manager for this request
#         db = DatabaseManager(db_path)
        
#         channel = db.fetchone(
#             "SELECT id, channel_id, channel_name, subscribers, description, url, scrape_time, thumbnail FROM channels WHERE id = ?",
#             (channel_id,)
#         )
        
#         if not channel:
#             return jsonify({"status": "error", "message": "Channel not found"}), 404
        
#         videos = db.fetchall(
#             """
#             SELECT v.id, v.video_id, v.title, v.views, v.upload_date, v.likes, v.thumbnail 
#             FROM videos v
#             WHERE v.channel_id = ?
#             ORDER BY v.upload_date DESC
#             """,
#             (channel_id,)
#         )
        
#         return jsonify({
#             "status": "success",
#             "channel": {
#                 "id": channel[0],
#                 "channel_id": channel[1],
#                 "name": channel[2],
#                 "subscribers": channel[3],
#                 "description": channel[4],
#                 "url": channel[5],
#                 "scrape_time": channel[6],
#                 "thumbnail": channel[7],
#                 "videos": [
#                     {
#                         "id": v[0],
#                         "video_id": v[1],
#                         "title": v[2],
#                         "views": v[3],
#                         "upload_date": v[4],
#                         "likes": v[5],
#                         "thumbnail": v[6]
#                     }
#                     for v in videos
#                 ]
#             }
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#     finally:
#         if db:
#             db.close()


# @app.route('/api/videos/<int:video_id>', methods=['GET'])
# def get_video(video_id: int) -> Response:
#     """Get video details including title and comment analysis."""
#     try:
#         # Create a new database manager for this request
#         db = DatabaseManager(db_path)
        
#         video = db.fetchone(
#             """
#             SELECT v.id, v.video_id, v.title, v.url, v.views, v.upload_date, v.likes, 
#                    v.description, v.thumbnail, c.channel_name, c.id
#             FROM videos v
#             JOIN channels c ON v.channel_id = c.id
#             WHERE v.id = ?
#             """,
#             (video_id,)
#         )
        
#         if not video:
#             return jsonify({"status": "error", "message": "Video not found"}), 404
        
#         # Get title analysis
#         title_analysis = db.fetchone(
#             """
#             SELECT id, highest_severity, analysis_results
#             FROM content_analysis
#             WHERE video_id = ? AND content_type = 'title' AND is_dangerous = 1
#             """,
#             (video_id,)
#         )
        
#         title_analysis_data = None
#         if title_analysis:
#             title_analysis_id = title_analysis[0]
#             # Get categories
#             categories = db.fetchall(
#                 """
#                 SELECT category_name, severity, keywords, count 
#                 FROM analysis_categories 
#                 WHERE analysis_id = ?
#                 """,
#                 (title_analysis_id,)
#             )
            
#             title_analysis_data = {
#                 "id": title_analysis[0],
#                 "highest_severity": title_analysis[1],
#                 "results": json.loads(title_analysis[2]),
#                 "categories": [
#                     {
#                         "name": c[0],
#                         "severity": c[1],
#                         "keywords": json.loads(c[2]),
#                         "count": c[3]
#                     }
#                     for c in categories
#                 ]
#             }
        
#         # Get comment analysis
#         comment_analysis = db.fetchone(
#             """
#             SELECT id, highest_severity, analysis_results
#             FROM content_analysis
#             WHERE video_id = ? AND content_type = 'comments' AND is_dangerous = 1
#             """,
#             (video_id,)
#         )
        
#         comment_analysis_data = None
#         if comment_analysis:
#             comment_analysis_id = comment_analysis[0]
#             # Get categories
#             categories = db.fetchall(
#                 """
#                 SELECT category_name, severity, keywords, count 
#                 FROM analysis_categories 
#                 WHERE analysis_id = ?
#                 """,
#                 (comment_analysis_id,)
#             )
            
#             comment_analysis_data = {
#                 "id": comment_analysis[0],
#                 "highest_severity": comment_analysis[1],
#                 "results": json.loads(comment_analysis[2]),
#                 "categories": [
#                     {
#                         "name": c[0],
#                         "severity": c[1],
#                         "keywords": json.loads(c[2]),
#                         "count": c[3]
#                     }
#                     for c in categories
#                 ]
#             }
        
#         # Get audio files
#         audio_files = db.fetchall(
#             "SELECT id, file_path, format_type, file_size, download_time FROM audio_files WHERE video_id = ?",
#             (video_id,)
#         )
        
#         # Get transcriptions
#         transcriptions = []
#         for audio in audio_files:
#             audio_id = audio[0]
#             trans = db.fetchall(
#                 "SELECT id, transcription_text, success, transcription_time FROM transcriptions WHERE audio_id = ?",
#                 (audio_id,)
#             )
            
#             for t in trans:
#                 trans_id = t[0]
#                 # Get content analysis
#                 analysis = db.fetchone(
#                     """
#                     SELECT id, is_dangerous, highest_severity, analysis_results 
#                     FROM content_analysis 
#                     WHERE transcription_id = ? AND content_type = 'transcription'
#                     """,
#                     (trans_id,)
#                 )
                
#                 analysis_data = None
#                 if analysis:
#                     analysis_id = analysis[0]
#                     # Get categories
#                     categories = db.fetchall(
#                         """
#                         SELECT category_name, severity, keywords, count 
#                         FROM analysis_categories 
#                         WHERE analysis_id = ?
#                         """,
#                         (analysis_id,)
#                     )
                    
#                     analysis_data = {
#                         "id": analysis[0],
#                         "is_dangerous": bool(analysis[1]),
#                         "highest_severity": analysis[2],
#                         "results": json.loads(analysis[3]),
#                         "categories": [
#                             {
#                                 "name": c[0],
#                                 "severity": c[1],
#                                 "keywords": json.loads(c[2]),
#                                 "count": c[3]
#                             }
#                             for c in categories
#                         ]
#                     }
                
#                 transcriptions.append({
#                     "id": t[0],
#                     "audio_id": audio_id,
#                     "text": t[1],
#                     "success": bool(t[2]),
#                     "time": t[3],
#                     "analysis": analysis_data
#                 })
        
#         # Get comments
#         comments = db.fetchall(
#             """
#             SELECT id, author, comment_text, likes, comment_date, is_verified, is_pinned 
#             FROM comments 
#             WHERE video_id = ?
#             ORDER BY id DESC
#             LIMIT 100
#             """,
#             (video_id,)
#         )
        
#         return jsonify({
#             "status": "success",
#             "video": {
#                 "id": video[0],
#                 "video_id": video[1],
#                 "title": video[2],
#                 "url": video[3],
#                 "views": video[4],
#                 "upload_date": video[5],
#                 "likes": video[6],
#                 "description": video[7],
#                 "thumbnail": video[8],
#                 "channel": {
#                     "name": video[9],
#                     "id": video[10]
#                 },
#                 "title_analysis": title_analysis_data,
#                 "comment_analysis": comment_analysis_data,
#                 "audio_files": [
#                     {
#                         "id": a[0],
#                         "file_path": a[1],
#                         "format_type": a[2],
#                         "file_size": a[3],
#                         "download_time": a[4]
#                     }
#                     for a in audio_files
#                 ],
#                 "transcriptions": transcriptions,
#                 "comments": [
#                     {
#                         "id": c[0],
#                         "author": c[1],
#                         "text": c[2],
#                         "likes": c[3],
#                         "date": c[4],
#                         "is_verified": bool(c[5]),
#                         "is_pinned": bool(c[6])
#                     }
#                     for c in comments
#                 ]
#             }
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#     finally:
#         if db:
#             db.close()


# @app.route('/api/process/channel', methods=['POST'])
# def process_channel() -> Response:
#     """Start processing a YouTube channel."""
#     try:
#         data = request.json
        
#         if not data or 'channel_input' not in data:
#             return jsonify({"status": "error", "message": "Missing required parameter: channel_input"}), 400
        
#         channel_input = data['channel_input']
#         max_videos = int(data.get('max_videos', 5))
#         scrape_comments = bool(data.get('scrape_comments', True))
#         min_severity = int(data.get('min_severity', 1))
        
#         task_id = str(uuid.uuid4())
        
#         # Create task record
#         active_tasks[task_id] = {
#             "status": "queued",
#             "type": "channel",
#             "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "params": {
#                 "channel_input": channel_input,
#                 "max_videos": max_videos,
#                 "scrape_comments": scrape_comments,
#                 "min_severity": min_severity
#             }
#         }
        
#         # Add task to queue
#         task_queue.put({
#             "id": task_id,
#             "type": "channel",
#             "params": {
#                 "channel_input": channel_input,
#                 "max_videos": max_videos,
#                 "scrape_comments": scrape_comments,
#                 "min_severity": min_severity
#             }
#         })
        
#         return jsonify({
#             "status": "success",
#             "message": "Channel processing queued",
#             "task_id": task_id
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


# @app.route('/api/process/video', methods=['POST'])
# def process_video() -> Response:
#     """Start processing a YouTube video."""
#     try:
#         data = request.json
        
#         if not data or 'video_url' not in data:
#             return jsonify({"status": "error", "message": "Missing required parameter: video_url"}), 400
        
#         video_url = data['video_url']
#         scrape_comments = bool(data.get('scrape_comments', True))
#         min_severity = int(data.get('min_severity', 1))
        
#         task_id = str(uuid.uuid4())
        
#         # Create task record
#         active_tasks[task_id] = {
#             "status": "queued",
#             "type": "video",
#             "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "params": {
#                 "video_url": video_url,
#                 "scrape_comments": scrape_comments,
#                 "min_severity": min_severity
#             }
#         }
        
#         # Add task to queue
#         task_queue.put({
#             "id": task_id,
#             "type": "video",
#             "params": {
#                 "video_url": video_url,
#                 "scrape_comments": scrape_comments,
#                 "min_severity": min_severity
#             }
#         })
        
#         return jsonify({
#             "status": "success",
#             "message": "Video processing queued",
#             "task_id": task_id
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500


# @app.route('/api/tasks', methods=['GET'])
# def get_tasks() -> Response:
#     """Get list of active and recent tasks."""
#     return jsonify({
#         "status": "success",
#         "tasks": active_tasks
#     })


# @app.route('/api/tasks/<task_id>', methods=['GET'])
# def get_task(task_id: str) -> Response:
#     """Get task status and results."""
#     if task_id not in active_tasks:
#         return jsonify({"status": "error", "message": "Task not found"}), 404
    
#     response = {
#         "status": "success",
#         "task": active_tasks[task_id]
#     }
    
#     # Include results if task is completed
#     if active_tasks[task_id]["status"] == "completed" and task_id in task_results:
#         response["results"] = task_results[task_id]
    
#     return jsonify(response)


# @app.route('/api/search', methods=['GET'])
# def search() -> Response:
#     """Search for channels and videos."""
#     query = request.args.get('q', '')
    
#     if not query or len(query) < 3:
#         return jsonify({
#             "status": "error", 
#             "message": "Search query must be at least 3 characters"
#         }), 400
    
#     try:
#         # Create a new database manager for this request
#         db = DatabaseManager(db_path)
        
#         # Search channels
#         channels = db.fetchall(
#             """
#             SELECT id, channel_id, channel_name, subscribers, url, thumbnail
#             FROM channels 
#             WHERE channel_name LIKE ? OR channel_id LIKE ?
#             LIMIT 10
#             """,
#             (f"%{query}%", f"%{query}%")
#         )
        
#         # Search videos
#         videos = db.fetchall(
#             """
#             SELECT v.id, v.video_id, v.title, v.thumbnail, c.channel_name 
#             FROM videos v
#             JOIN channels c ON v.channel_id = c.id
#             WHERE v.title LIKE ? OR v.description LIKE ?
#             LIMIT 20
#             """,
#             (f"%{query}%", f"%{query}%")
#         )
        
#         # Search transcriptions
#         transcriptions = db.fetchall(
#             """
#             SELECT t.id, t.transcription_text, v.id, v.title
#             FROM transcriptions t
#             JOIN audio_files a ON t.audio_id = a.id
#             JOIN videos v ON a.video_id = v.id
#             WHERE t.transcription_text LIKE ?
#             LIMIT 20
#             """,
#             (f"%{query}%",)
#         )
        
#         return jsonify({
#             "status": "success",
#             "results": {
#                 "channels": [
#                     {
#                         "id": c[0],
#                         "channel_id": c[1],
#                         "name": c[2],
#                         "subscribers": c[3],
#                         "url": c[4],
#                         "thumbnail": c[5]
#                     }
#                     for c in channels
#                 ],
#                 "videos": [
#                     {
#                         "id": v[0],
#                         "video_id": v[1],
#                         "title": v[2],
#                         "thumbnail": v[3],
#                         "channel_name": v[4]
#                     }
#                     for v in videos
#                 ],
#                 "transcriptions": [
#                     {
#                         "id": t[0],
#                         "excerpt": t[1][:150] + "..." if len(t[1]) > 150 else t[1],
#                         "video_id": t[2],
#                         "video_title": t[3]
#                     }
#                     for t in transcriptions
#                 ]
#             }
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#     finally:
#         if db:
#             db.close()


# @app.route('/api/stats', methods=['GET'])
# def get_stats() -> Response:
#     """Get server statistics."""
#     try:
#         # Create a new database manager for this request
#         db = DatabaseManager(db_path)
        
#         stats = {
#             "channels_count": db.fetchone("SELECT COUNT(*) FROM channels")[0],
#             "videos_count": db.fetchone("SELECT COUNT(*) FROM videos")[0],
#             "transcriptions_count": db.fetchone("SELECT COUNT(*) FROM transcriptions")[0],
#             "dangerous_content_count": db.fetchone("SELECT COUNT(*) FROM content_analysis WHERE is_dangerous = 1")[0],
#             "dangerous_titles_count": db.fetchone("SELECT COUNT(*) FROM content_analysis WHERE is_dangerous = 1 AND content_type = 'title'")[0],
#             "dangerous_comments_count": db.fetchone("SELECT COUNT(*) FROM content_analysis WHERE is_dangerous = 1 AND content_type = 'comments'")[0],
#             "active_tasks": len([t for t in active_tasks.values() if t["status"] == "in_progress"]),
#             "queued_tasks": task_queue.qsize(),
#             "completed_tasks": len([t for t in active_tasks.values() if t["status"] == "completed"]),
#             "failed_tasks": len([t for t in active_tasks.values() if t["status"] == "failed"]),
#             "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#             "dangerous_categories": db.fetchall("""
#                 SELECT category_name, COUNT(*) as count 
#                 FROM analysis_categories 
#                 GROUP BY category_name 
#                 ORDER BY count DESC
#             """),
#             "dangerous_categories_by_content_type": {
#                 "title": db.fetchall("""
#                     SELECT ac.category_name, COUNT(*) as count 
#                     FROM analysis_categories ac
#                     JOIN content_analysis ca ON ac.analysis_id = ca.id
#                     WHERE ca.content_type = 'title'
#                     GROUP BY ac.category_name 
#                     ORDER BY count DESC
#                 """),
#                 "comments": db.fetchall("""
#                     SELECT ac.category_name, COUNT(*) as count 
#                     FROM analysis_categories ac
#                     JOIN content_analysis ca ON ac.analysis_id = ca.id
#                     WHERE ca.content_type = 'comments'
#                     GROUP BY ac.category_name 
#                     ORDER BY count DESC
#                 """),
#                 "transcription": db.fetchall("""
#                     SELECT ac.category_name, COUNT(*) as count 
#                     FROM analysis_categories ac
#                     JOIN content_analysis ca ON ac.analysis_id = ca.id
#                     WHERE ca.content_type = 'transcription'
#                     GROUP BY ac.category_name 
#                     ORDER BY count DESC
#                 """)
#             }
#         }
        
#         return jsonify({
#             "status": "success",
#             "stats": stats
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#     finally:
#         if db:
#             db.close()
            

# @app.route('/api/analysis/dangerous-videos', methods=['GET'])
# def get_dangerous_videos() -> Response:
#     """Get videos with dangerous content, filtered by content type."""
#     try:
#         content_type = request.args.get('content_type', None)  # 'title', 'comments', 'transcription', or None for all
        
#         # Create a new database manager for this request
#         db = DatabaseManager(db_path)
        
#         query = """
#             SELECT v.id, v.title, v.thumbnail, c.channel_name, 
#                    ca.content_type, ca.highest_severity, ca.analysis_results
#             FROM videos v
#             JOIN channels c ON v.channel_id = c.id
#             JOIN content_analysis ca ON ca.video_id = v.id
#             WHERE ca.is_dangerous = 1
#         """
        
#         params = ()
#         if content_type:
#             query += " AND ca.content_type = ?"
#             params = (content_type,)
            
#         query += " ORDER BY ca.highest_severity DESC, ca.analysis_time DESC LIMIT 50"
        
#         videos = db.fetchall(query, params)
        
#         results = []
#         for v in videos:
#             analysis_results = json.loads(v[6])
            
#             # Get the categories for this analysis
#             analysis_id = db.fetchone(
#                 "SELECT id FROM content_analysis WHERE video_id = ? AND content_type = ?",
#                 (v[0], v[4])
#             )[0]
            
#             categories = db.fetchall(
#                 """
#                 SELECT category_name, severity, keywords
#                 FROM analysis_categories
#                 WHERE analysis_id = ?
#                 """,
#                 (analysis_id,)
#             )
            
#             results.append({
#                 "id": v[0],
#                 "title": v[1],
#                 "thumbnail": v[2],
#                 "channel_name": v[3],
#                 "content_type": v[4],
#                 "highest_severity": v[5],
#                 "analysis_summary": {
#                     "categories": [
#                         {
#                             "name": c[0],
#                             "severity": c[1],
#                             "keywords": json.loads(c[2])
#                         }
#                         for c in categories
#                     ]
#                 }
#             })
        
#         return jsonify({
#             "status": "success",
#             "videos": results
#         })
#     except Exception as e:
#         return jsonify({"status": "error", "message": str(e)}), 500
#     finally:
#         if db:
#             db.close()

# def main():
#     """Main function to run the server."""
#     parser = argparse.ArgumentParser(description='YouTube Analysis Server')
#     parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host')
#     parser.add_argument('--port', type=int, default=5001, help='Server port')
#     parser.add_argument('--db', type=str, default='db/youtube_analysis.db', help='Path to SQLite database file')
#     parser.add_argument('--output', type=str, default='downloads', help='Output folder for downloaded files')
#     parser.add_argument('--schema', type=str, default='db/schema.sql', help='Path to database schema file')
#     parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
#     args = parser.parse_args()
    
#     # Initialize server components
#     initialize_server(args.db, args.output, args.schema)
    
#     try:
#         # Run the Flask server
#         app.run(host=args.host, port=args.port, debug=args.debug)
#     finally:
#         # Clean up resources when server stops
#         global running
#         running = False
        
#         if worker_thread:
#             worker_thread.join(timeout=5.0)
            
#         if pipeline_manager:
#             pipeline_manager.close()
            
#         print("Server stopped")


# if __name__ == "__main__":
#     main()

import os
import json
import argparse
from typing import Dict, Any, List, Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import threading
import uuid
import time
from datetime import datetime
import queue
import traceback

# Import our pipeline components
from db.db_setup import DatabaseManager, create_schema_file
from modules.core_modules import PipelineManager

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global variables
pipeline_manager = None
db_path = None
output_folder = None
active_tasks = {}
task_results = {}
task_queue = queue.Queue()
worker_thread = None
running = True

def worker_function():
    """Worker thread that processes tasks from the queue."""
    global running, pipeline_manager, db_path, output_folder
    
    while running:
        try:
            # Get task from queue with timeout
            try:
                task = task_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            
            task_id = task["id"]
            task_type = task["type"]
            
            # Create a new pipeline manager for this task
            # This ensures each task has its own database connection
            task_pipeline = PipelineManager(db_path, output_folder)
            
            try:
                if task_type == "channel":
                    active_tasks[task_id]["status"] = "in_progress"
                    
                    # Process channel
                    channel_input = task["params"]["channel_input"]
                    max_videos = task["params"]["max_videos"]
                    scrape_comments = task["params"]["scrape_comments"]
                    min_severity = task["params"]["min_severity"]
                    
                    results = task_pipeline.process_channel(
                        channel_input, max_videos, scrape_comments, min_severity
                    )
                    
                    active_tasks[task_id]["status"] = "completed"
                    active_tasks[task_id]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    task_results[task_id] = results
                
                elif task_type == "video":
                    active_tasks[task_id]["status"] = "in_progress"
                    
                    # Process video
                    video_url = task["params"]["video_url"]
                    scrape_comments = task["params"]["scrape_comments"]
                    min_severity = task["params"]["min_severity"]
                    
                    results = task_pipeline.process_video(
                        video_url, scrape_comments, min_severity
                    )
                    
                    active_tasks[task_id]["status"] = "completed"
                    active_tasks[task_id]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    task_results[task_id] = results
            
            except Exception as e:
                error_msg = f"Error processing task: {e}\n{traceback.format_exc()}"
                print(error_msg)
                active_tasks[task_id]["status"] = "failed"
                active_tasks[task_id]["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                active_tasks[task_id]["error"] = str(e)
                task_results[task_id] = {"errors": [str(e)]}
            
            finally:
                # Clean up resources
                if task_pipeline:
                    task_pipeline.close()
                
                # Mark task as done
                task_queue.task_done()
        
        except Exception as e:
            print(f"Error in worker thread: {e}")
            time.sleep(1)  # Prevent tight loop in case of repeated errors

def initialize_server(db_file_path: str, output_dir: str, schema_path: str) -> None:
    """
    Initialize the server components.
    
    Args:
        db_file_path: Path to the SQLite database file
        output_dir: Folder to store downloaded files
        schema_path: Path to the database schema file
    """
    global pipeline_manager, db_path, output_folder, worker_thread
    
    # Save paths for worker threads
    db_path = db_file_path
    output_folder = output_dir
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Create database schema file if it doesn't exist
    if not os.path.exists(schema_path):
        with open('db/schema.sql', 'r') as f:
            schema_content = f.read()
        create_schema_file(schema_content, schema_path)
    
    # Initialize pipeline manager for API requests that don't require a worker thread
    pipeline_manager = PipelineManager(db_path, output_folder)
    
    # Start worker thread
    worker_thread = threading.Thread(target=worker_function)
    worker_thread.daemon = True
    worker_thread.start()
    
    print(f"Server initialized with database at {db_path} and output folder at {output_folder}")


# API Routes

@app.route('/api/health', methods=['GET'])
def health_check() -> Response:
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_tasks": len(active_tasks),
        "queued_tasks": task_queue.qsize()
    })


@app.route('/api/channels', methods=['GET'])
def get_channels() -> Response:
    """Get list of channels."""
    try:
        # Create a new database manager for this request
        db = DatabaseManager(db_path)
        
        channels = db.fetchall(
            "SELECT id, channel_id, channel_name, subscribers, url, scrape_time, thumbnail FROM channels ORDER BY scrape_time DESC"
        )
        
        return jsonify({
            "status": "success",
            "channels": [
                {
                    "id": c[0],
                    "channel_id": c[1],
                    "name": c[2],
                    "subscribers": c[3],
                    "url": c[4],
                    "scrape_time": c[5],
                    "thumbnail": c[6]
                } 
                for c in channels
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/channels/<int:channel_id>', methods=['GET'])
def get_channel(channel_id: int) -> Response:
    """Get channel details."""
    try:
        # Create a new database manager for this request
        db = DatabaseManager(db_path)
        
        channel = db.fetchone(
            "SELECT id, channel_id, channel_name, subscribers, description, url, scrape_time, thumbnail FROM channels WHERE id = ?",
            (channel_id,)
        )
        
        if not channel:
            return jsonify({"status": "error", "message": "Channel not found"}), 404
        
        videos = db.fetchall(
            """
            SELECT v.id, v.video_id, v.title, v.views, v.upload_date, v.likes, v.thumbnail 
            FROM videos v
            WHERE v.channel_id = ?
            ORDER BY v.upload_date DESC
            """,
            (channel_id,)
        )
        
        return jsonify({
            "status": "success",
            "channel": {
                "id": channel[0],
                "channel_id": channel[1],
                "name": channel[2],
                "subscribers": channel[3],
                "description": channel[4],
                "url": channel[5],
                "scrape_time": channel[6],
                "thumbnail": channel[7],
                "videos": [
                    {
                        "id": v[0],
                        "video_id": v[1],
                        "title": v[2],
                        "views": v[3],
                        "upload_date": v[4],
                        "likes": v[5],
                        "thumbnail": v[6]
                    }
                    for v in videos
                ]
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/videos/<int:video_id>', methods=['GET'])
def get_video(video_id: int) -> Response:
    """Get video details including title and comment analysis."""
    try:
        # Create a new database manager for this request
        db = DatabaseManager(db_path)
        
        video = db.fetchone(
            """
            SELECT v.id, v.video_id, v.title, v.url, v.views, v.upload_date, v.likes, 
                   v.description, v.thumbnail, c.channel_name, c.id
            FROM videos v
            JOIN channels c ON v.channel_id = c.id
            WHERE v.id = ?
            """,
            (video_id,)
        )
        
        if not video:
            return jsonify({"status": "error", "message": "Video not found"}), 404
        
        # Get title analysis
        title_analysis = db.fetchone(
            """
            SELECT id, highest_severity, analysis_results
            FROM content_analysis
            WHERE video_id = ? AND content_type = 'title' AND is_dangerous = 1
            """,
            (video_id,)
        )
        
        title_analysis_data = None
        if title_analysis:
            title_analysis_data = {
                "id": title_analysis[0],
                "highest_severity": title_analysis[1],
                "results": json.loads(title_analysis[2])
            }
        
        # Get comment analysis
        comment_analysis = db.fetchone(
            """
            SELECT id, highest_severity, analysis_results
            FROM content_analysis
            WHERE video_id = ? AND content_type = 'comments' AND is_dangerous = 1
            """,
            (video_id,)
        )
        
        comment_analysis_data = None
        if comment_analysis:
            comment_analysis_data = {
                "id": comment_analysis[0],
                "highest_severity": comment_analysis[1],
                "results": json.loads(comment_analysis[2])
            }
        
        # Get audio files
        audio_files = db.fetchall(
            "SELECT id, file_path, format_type, file_size, download_time FROM audio_files WHERE video_id = ?",
            (video_id,)
        )
        
        # Get transcriptions
        transcriptions = []
        for audio in audio_files:
            audio_id = audio[0]
            trans = db.fetchall(
                "SELECT id, transcription_text, success, transcription_time FROM transcriptions WHERE audio_id = ?",
                (audio_id,)
            )
            
            for t in trans:
                trans_id = t[0]
                # Get content analysis
                analysis = db.fetchone(
                    """
                    SELECT id, is_dangerous, highest_severity, analysis_results 
                    FROM content_analysis 
                    WHERE transcription_id = ? AND content_type = 'transcription'
                    """,
                    (trans_id,)
                )
                
                analysis_data = None
                if analysis:
                    analysis_data = {
                        "id": analysis[0],
                        "is_dangerous": bool(analysis[1]),
                        "highest_severity": analysis[2],
                        "results": json.loads(analysis[3])
                    }
                
                transcriptions.append({
                    "id": t[0],
                    "audio_id": audio_id,
                    "text": t[1],
                    "success": bool(t[2]),
                    "time": t[3],
                    "analysis": analysis_data
                })
        
        # Get comments
        comments = db.fetchall(
            """
            SELECT id, author, comment_text, likes, comment_date, is_verified, is_pinned 
            FROM comments 
            WHERE video_id = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (video_id,)
        )
        
        return jsonify({
            "status": "success",
            "video": {
                "id": video[0],
                "video_id": video[1],
                "title": video[2],
                "url": video[3],
                "views": video[4],
                "upload_date": video[5],
                "likes": video[6],
                "description": video[7],
                "thumbnail": video[8],
                "channel": {
                    "name": video[9],
                    "id": video[10]
                },
                "title_analysis": title_analysis_data,
                "comment_analysis": comment_analysis_data,
                "audio_files": [
                    {
                        "id": a[0],
                        "file_path": a[1],
                        "format_type": a[2],
                        "file_size": a[3],
                        "download_time": a[4]
                    }
                    for a in audio_files
                ],
                "transcriptions": transcriptions,
                "comments": [
                    {
                        "id": c[0],
                        "author": c[1],
                        "text": c[2],
                        "likes": c[3],
                        "date": c[4],
                        "is_verified": bool(c[5]),
                        "is_pinned": bool(c[6])
                    }
                    for c in comments
                ]
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/process/channel', methods=['POST'])
def process_channel() -> Response:
    """Start processing a YouTube channel."""
    try:
        data = request.json
        
        if not data or 'channel_input' not in data:
            return jsonify({"status": "error", "message": "Missing required parameter: channel_input"}), 400
        
        channel_input = data['channel_input']
        max_videos = int(data.get('max_videos', 5))
        scrape_comments = bool(data.get('scrape_comments', True))
        min_severity = int(data.get('min_severity', 1))
        
        task_id = str(uuid.uuid4())
        
        # Create task record
        active_tasks[task_id] = {
            "status": "queued",
            "type": "channel",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "params": {
                "channel_input": channel_input,
                "max_videos": max_videos,
                "scrape_comments": scrape_comments,
                "min_severity": min_severity
            }
        }
        
        # Add task to queue
        task_queue.put({
            "id": task_id,
            "type": "channel",
            "params": {
                "channel_input": channel_input,
                "max_videos": max_videos,
                "scrape_comments": scrape_comments,
                "min_severity": min_severity
            }
        })
        
        return jsonify({
            "status": "success",
            "message": "Channel processing queued",
            "task_id": task_id
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/process/video', methods=['POST'])
def process_video() -> Response:
    """Start processing a YouTube video."""
    try:
        data = request.json
        
        if not data or 'video_url' not in data:
            return jsonify({"status": "error", "message": "Missing required parameter: video_url"}), 400
        
        video_url = data['video_url']
        scrape_comments = bool(data.get('scrape_comments', True))
        min_severity = int(data.get('min_severity', 1))
        
        task_id = str(uuid.uuid4())
        
        # Create task record
        active_tasks[task_id] = {
            "status": "queued",
            "type": "video",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "params": {
                "video_url": video_url,
                "scrape_comments": scrape_comments,
                "min_severity": min_severity
            }
        }
        
        # Add task to queue
        task_queue.put({
            "id": task_id,
            "type": "video",
            "params": {
                "video_url": video_url,
                "scrape_comments": scrape_comments,
                "min_severity": min_severity
            }
        })
        
        return jsonify({
            "status": "success",
            "message": "Video processing queued",
            "task_id": task_id
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks() -> Response:
    """Get list of active and recent tasks."""
    return jsonify({
        "status": "success",
        "tasks": active_tasks
    })


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task(task_id: str) -> Response:
    """Get task status and results."""
    if task_id not in active_tasks:
        return jsonify({"status": "error", "message": "Task not found"}), 404
    
    response = {
        "status": "success",
        "task": active_tasks[task_id]
    }
    
    # Include results if task is completed
    if active_tasks[task_id]["status"] == "completed" and task_id in task_results:
        response["results"] = task_results[task_id]
    
    return jsonify(response)


@app.route('/api/search', methods=['GET'])
def search() -> Response:
    """Search for channels and videos."""
    query = request.args.get('q', '')
    
    if not query or len(query) < 3:
        return jsonify({
            "status": "error", 
            "message": "Search query must be at least 3 characters"
        }), 400
    
    try:
        # Create a new database manager for this request
        db = DatabaseManager(db_path)
        
        # Search channels
        channels = db.fetchall(
            """
            SELECT id, channel_id, channel_name, subscribers, url, thumbnail
            FROM channels 
            WHERE channel_name LIKE ? OR channel_id LIKE ?
            LIMIT 10
            """,
            (f"%{query}%", f"%{query}%")
        )
        
        # Search videos
        videos = db.fetchall(
            """
            SELECT v.id, v.video_id, v.title, v.thumbnail, c.channel_name 
            FROM videos v
            JOIN channels c ON v.channel_id = c.id
            WHERE v.title LIKE ? OR v.description LIKE ?
            LIMIT 20
            """,
            (f"%{query}%", f"%{query}%")
        )
        
        # Search transcriptions
        transcriptions = db.fetchall(
            """
            SELECT t.id, t.transcription_text, v.id, v.title
            FROM transcriptions t
            JOIN audio_files a ON t.audio_id = a.id
            JOIN videos v ON a.video_id = v.id
            WHERE t.transcription_text LIKE ?
            LIMIT 20
            """,
            (f"%{query}%",)
        )
        
        return jsonify({
            "status": "success",
            "results": {
                "channels": [
                    {
                        "id": c[0],
                        "channel_id": c[1],
                        "name": c[2],
                        "subscribers": c[3],
                        "url": c[4],
                        "thumbnail": c[5]
                    }
                    for c in channels
                ],
                "videos": [
                    {
                        "id": v[0],
                        "video_id": v[1],
                        "title": v[2],
                        "thumbnail": v[3],
                        "channel_name": v[4]
                    }
                    for v in videos
                ],
                "transcriptions": [
                    {
                        "id": t[0],
                        "excerpt": t[1][:150] + "..." if len(t[1]) > 150 else t[1],
                        "video_id": t[2],
                        "video_title": t[3]
                    }
                    for t in transcriptions
                ]
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()


@app.route('/api/stats', methods=['GET'])
def get_stats() -> Response:
    """Get server statistics."""
    try:
        # Create a new database manager for this request
        db = DatabaseManager(db_path)
        
        stats = {
            "channels_count": db.fetchone("SELECT COUNT(*) FROM channels")[0],
            "videos_count": db.fetchone("SELECT COUNT(*) FROM videos")[0],
            "transcriptions_count": db.fetchone("SELECT COUNT(*) FROM transcriptions")[0],
            "dangerous_content_count": db.fetchone("SELECT COUNT(*) FROM content_analysis WHERE is_dangerous = 1")[0],
            "dangerous_titles_count": db.fetchone("SELECT COUNT(*) FROM content_analysis WHERE is_dangerous = 1 AND content_type = 'title'")[0],
            "dangerous_comments_count": db.fetchone("SELECT COUNT(*) FROM content_analysis WHERE is_dangerous = 1 AND content_type = 'comments'")[0],
            "active_tasks": len([t for t in active_tasks.values() if t["status"] == "in_progress"]),
            "queued_tasks": task_queue.qsize(),
            "completed_tasks": len([t for t in active_tasks.values() if t["status"] == "completed"]),
            "failed_tasks": len([t for t in active_tasks.values() if t["status"] == "failed"]),
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return jsonify({
            "status": "success",
            "stats": stats
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()
            

@app.route('/api/analysis/dangerous-videos', methods=['GET'])
def get_dangerous_videos() -> Response:
    """Get videos with dangerous content, filtered by content type."""
    try:
        content_type = request.args.get('content_type', None)  # 'title', 'comments', 'transcription', or None for all
        
        # Create a new database manager for this request
        db = DatabaseManager(db_path)
        
        query = """
            SELECT v.id, v.title, v.thumbnail, c.channel_name, 
                   ca.content_type, ca.highest_severity, ca.analysis_results
            FROM videos v
            JOIN channels c ON v.channel_id = c.id
            JOIN content_analysis ca ON ca.video_id = v.id
            WHERE ca.is_dangerous = 1
        """
        
        params = ()
        if content_type:
            query += " AND ca.content_type = ?"
            params = (content_type,)
            
        query += " ORDER BY ca.highest_severity DESC, ca.analysis_time DESC LIMIT 50"
        
        videos = db.fetchall(query, params)
        
        results = []
        for v in videos:
            analysis_results = json.loads(v[6])
            
            results.append({
                "id": v[0],
                "title": v[1],
                "thumbnail": v[2],
                "channel_name": v[3],
                "content_type": v[4],
                "highest_severity": v[5],
                "analysis_summary": analysis_results
            })
        
        return jsonify({
            "status": "success",
            "videos": results
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if db:
            db.close()

def main():
    """Main function to run the server."""
    parser = argparse.ArgumentParser(description='YouTube Analysis Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Server host')
    parser.add_argument('--port', type=int, default=5001, help='Server port')
    parser.add_argument('--db', type=str, default='db/youtube_analysis.db', help='Path to SQLite database file')
    parser.add_argument('--output', type=str, default='downloads', help='Output folder for downloaded files')
    parser.add_argument('--schema', type=str, default='db/schema.sql', help='Path to database schema file')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Initialize server components
    initialize_server(args.db, args.output, args.schema)
    
    try:
        # Run the Flask server
        app.run(host=args.host, port=args.port, debug=args.debug)
    finally:
        # Clean up resources when server stops
        global running
        running = False
        
        if worker_thread:
            worker_thread.join(timeout=5.0)
            
        if pipeline_manager:
            pipeline_manager.close()
            
        print("Server stopped")


if __name__ == "__main__":
    main()