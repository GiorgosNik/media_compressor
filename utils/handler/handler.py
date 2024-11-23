import os
from datetime import datetime
from utils.video.video_compressor import VideoCompressor


class Handler:
    @classmethod
    def start_compression(cls, input_directory, progress_callback=None):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_directory = f"{input_directory}/output_{timestamp}"
        os.makedirs(output_directory, exist_ok=True)
        VideoCompressor.compress_videos_in_directory(input_directory, output_directory, progress_callback)