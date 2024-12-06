import os
from datetime import datetime
from utils.video.video_compressor import VideoCompressor
from utils.images.image_compressor import ImageCompressor
from utils.logging.logging import setup_logging
import logging


class Handler:
    LOGGER = None

    @classmethod
    def start_compression(cls, input_directory, process_video, process_image, convert_incompatible, progress_callback=None):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        output_directory = f"{input_directory}/output_{timestamp}"
        os.makedirs(output_directory, exist_ok=True)

        setup_logging(output_directory)
        cls.LOGGER = logging.getLogger(__name__)
        cls.LOGGER.info(f"Output directory created: {output_directory}")

        if process_video:
            VideoCompressor.compress_videos_in_directory(input_directory, output_directory, progress_callback)
        if process_image:
            ImageCompressor.compress_images_in_directory(input_directory, output_directory, progress_callback)
        if convert_incompatible:
           VideoCompressor.convert_incompatible_videos_in_directory_and_compress(input_directory, output_directory, progress_callback)