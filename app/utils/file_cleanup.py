import os


def cleanup_temp_files(file_paths):
    """
    Delete temporary files to free up space.
    """
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.remove(file_path)









# def search_transcript(transcript: list, query: str) -> list:
#     results = []
#     for segment in transcript:
#         if query.lower() in segment['text'].lower():
#             results.append({
#                 "text": segment['text'],
#                 "start": segment['start'],
#                 "duration": segment['duration']
#             })
#     return results
