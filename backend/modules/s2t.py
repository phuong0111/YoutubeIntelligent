# import os
# from pydub import AudioSegment
# import torch
# import warnings
# from transformers import pipeline
# warnings.filterwarnings("ignore")

# def convert_mp3_to_wav(mp3_path):
#     """
#     Convert an MP3 file to WAV format using pydub
    
#     Parameters:
#     mp3_path (str): Path to the MP3 file
    
#     Returns:
#     str: Path to the converted WAV file
#     """
#     wav_path = os.path.splitext(mp3_path)[0] + ".wav"
    
#     # Load the MP3 file
#     sound = AudioSegment.from_mp3(mp3_path)
    
#     # Convert to 16kHz sample rate (required for Whisper models)
#     sound = sound.set_frame_rate(16000)
    
#     # Export as WAV
#     sound.export(wav_path, format="wav")
    
#     return wav_path

# def transcribe_vietnamese_audio(file_path, chunk_size=None):
#     """
#     Transcribe Vietnamese speech from an audio file using VINAI/PhoWhisper-medium.
    
#     Parameters:
#     file_path (str): Path to the audio file (WAV or MP3)
#     chunk_size (int, optional): Size of audio chunks in milliseconds for chunking long audio
    
#     Returns:
#     dict: Dictionary containing success status, error (if any), and transcription
#     """
#     # Set up the response object
#     response = {
#         "success": True,
#         "error": None,
#         "transcription": None
#     }
    
#     # Check if the file is MP3, convert to WAV if needed
#     if file_path.lower().endswith('.mp3'):
#         print(f"Đang chuyển đổi tệp MP3 sang định dạng WAV 16kHz...")
#         file_path = convert_mp3_to_wav(file_path)
    
#     try:
        
#         # Create the pipeline with the PhoWhisper model
#         # Enable return_timestamps for long audio files
#         transcriber = pipeline("automatic-speech-recognition", 
#                                model="vinai/PhoWhisper-medium",
#                                chunk_length_s=30,  # Process 30 seconds at a time
#                                return_timestamps=True)  # Enable timestamp tokens for long audio
        
#         # Transcribe the audio
#         print(f"Đang phiên âm tệp: {file_path}...")
#         output = transcriber(file_path)
        
#         # Extract the transcription text
#         # If output is a dictionary with 'text' key, use that
#         if isinstance(output, dict) and 'text' in output:
#             response["transcription"] = output['text']
#         # If output is a dictionary with 'chunks' key, combine the text from all chunks
#         elif isinstance(output, dict) and 'chunks' in output:
#             chunks_text = [chunk['text'] for chunk in output['chunks']]
#             response["transcription"] = ' '.join(chunks_text)
#         # Fallback case - try to convert output to string
#         else:
#             response["transcription"] = str(output)
        
#     except Exception as e:
#         response["success"] = False
#         response["error"] = f"Lỗi xử lý: {str(e)}"
        
#         # Provide more specific error details and help
#         if "CUDA" in str(e):
#             response["error"] += "\nLỗi liên quan đến GPU. Thử thêm: device='cpu' khi tải mô hình."
#         elif "Memory" in str(e) or "memory" in str(e):
#             response["error"] += "\nLỗi thiếu bộ nhớ. Thử mô hình nhỏ hơn như 'base' hoặc sử dụng thiết bị có nhiều RAM hơn."
    
#     return response

# if __name__ == "__main__":
#     import argparse
    
#     # Create argument parser
#     parser = argparse.ArgumentParser(description='Phiên âm tiếng Việt từ tệp âm thanh sử dụng VINAI/PhoWhisper-medium')
#     parser.add_argument('--file-path', type=str, help='Đường dẫn đến tệp âm thanh (WAV hoặc MP3)')
    
#     # Parse arguments
#     args = parser.parse_args()
    
#     # Call the transcribe function
#     print(f"Đang chuẩn bị phiên âm tệp âm thanh: {args.file_path}")
#     result = transcribe_vietnamese_audio(args.file_path)
    
#     # Display the results
#     if result["success"] and result["transcription"]:
#         print("\nPhiên âm:")
#         print(result["transcription"])