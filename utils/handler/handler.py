import os
from datetime import datetime
from utils.video.video_compressor import VideoCompressor
from utils.images.image_compressor import ImageCompressor
from utils.logging.logging import setup_logging
import logging


class Handler:
    LOGGER = None

    @classmethod
    def get_directory_size(cls, directory):
        """Calculate total size of a directory in bytes"""
        total_size = 0
        if os.path.isfile(directory):
            return os.path.getsize(directory)
        
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    @classmethod
    def start_compression(cls, input_directory, process_video, process_image, convert_incompatible, progress_callback=None):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        
        # Get initial size before compression
        original_size = cls.get_directory_size(input_directory)
        
        if os.path.isfile(input_directory):
            output_directory = f"{os.path.dirname(input_directory)}/output_{timestamp}"
        else:
            output_directory = f"{input_directory}/output_{timestamp}"
            
        os.makedirs(output_directory, exist_ok=True)

        setup_logging(output_directory)
        cls.LOGGER = logging.getLogger(__name__)
        cls.LOGGER.info(f"Output directory created: {output_directory}")

        try:
            if process_video:
                VideoCompressor.compress_videos_in_directory(input_directory, output_directory, progress_callback)
            if process_image:
                ImageCompressor.compress_images_in_directory(input_directory, output_directory, progress_callback)
            if convert_incompatible:
                VideoCompressor.convert_incompatible_videos_in_directory_and_compress(input_directory, output_directory, progress_callback)
                
            compressed_size = cls.get_directory_size(output_directory)
            return original_size, compressed_size,
        finally:
            cls.cleanup_logging()

    @classmethod
    def cleanup_logging(cls):
        """Close all logging handlers"""
        if cls.LOGGER:
            for handler in cls.LOGGER.handlers[:]:
                handler.close()
                cls.LOGGER.removeHandler(handler)
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)