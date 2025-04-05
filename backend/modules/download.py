# from __future__ import unicode_literals
# import os
# import json
# import yt_dlp
# import argparse

# def download_audio_from_id(video_id, output_folder, format_type="mp3"):
#     """
#     Download audio from a YouTube video ID using yt-dlp.
    
#     Args:
#         video_id: YouTube video ID
#         output_folder: Folder to save the downloaded audio
#         format_type: Audio format (default: "mp3")
        
#     Returns:
#         bool: True if download was successful, False otherwise
#     """
#     try:
#         # Create output folder if it doesn't exist
#         os.makedirs(output_folder, exist_ok=True)
        
#         # Create YouTube URL from video ID
#         url = f"https://www.youtube.com/watch?v={video_id}"
        
#         # Create the output filename without extension
#         # yt-dlp will add the extension based on the format
#         filename = os.path.join(output_folder, video_id)
        
#         # Configure yt-dlp options
#         ydl_opts = {
#             'format': 'bestaudio/best',
#             'outtmpl': filename,
#             'postprocessors': [{
#                 'key': 'FFmpegExtractAudio',
#                 'preferredcodec': format_type,
#                 'preferredquality': '192',
#             }],
#             'quiet': False,
#             'no_warnings': False,
#             'cookiefile': 'cookies.txt'
#         }
        
#         # Download the audio
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([url])
            
#         print(f"Downloaded: {video_id}.{format_type}")
#         return True
        
#     except Exception as e:
#         print(f"Error downloading video ID {video_id}: {e}")
#         return False
    
# # Main execution
# if __name__ == "__main__":
#     parser = argparse.ArgumentParser(description='Download audio from YouTube video IDs')
#     parser.add_argument('--id', type=str, required=True, help='Single YouTube video ID to download')
#     parser.add_argument('--output', type=str, default='downloads', help='Output folder')
#     parser.add_argument('--format', type=str, default='mp3', help='Audio format (mp3, wav, etc.)')
    
#     args = parser.parse_args()

#     download_audio_from_id(args.id, args.output, args.format)