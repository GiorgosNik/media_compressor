import os
from datetime import datetime
from utils.video.video_compressor import VideoCompressor
from utils.images.image_compressor import ImageCompressor
from utils.logging.logging import setup_logging
import logging


class Handler:
    setup_logging()  # Set up logging configuration
    LOGGER = logging.getLogger(__name__)
    
    @classmethod
    def start_compression(cls, input_directory, progress_callback=None):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        output_directory = f"{input_directory}/output_{timestamp}"
        os.makedirs(output_directory, exist_ok=True)
        cls.LOGGER.info(f"Output directory created: {output_directory}")
        VideoCompressor.compress_videos_in_directory(input_directory, output_directory, progress_callback)
        ImageCompressor.compress_images_in_directory(input_directory, output_directory, progress_callback)