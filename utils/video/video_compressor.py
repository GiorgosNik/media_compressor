import json
import subprocess
import sys
import ffmpeg
import os
from utils.video.config import VIDEO_FILETYPES
from utils.video.config import VIDEO_CODECS
from utils.logging.logging import setup_logging
import logging


class VideoCompressor:
    FRAMERATE = 29.97
    LOGGER = None

    @classmethod
    def run_subprocess_with_flags(cls, cmd, **kwargs):
        if sys.platform == 'win32':
            kwargs['encoding'] = 'utf-8'
            kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW
        return subprocess.run(cmd, **kwargs)

    @classmethod
    def is_video_processed(cls, file_path):
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_format',
                '-show_streams',
                '-print_format', 'json',
                file_path
            ]
            result = cls.run_subprocess_with_flags(
                cmd,
                capture_output=True,
                text=True
            )
            metadata = json.loads(result.stdout)
            vid_tags = metadata.get("format", {}).get("tags", {})
            return vid_tags.get("comment") == "compressed"
        except Exception as e:
            cls.LOGGER.error(
                f"Error while parsing metadata for video:{file_path}. ERROR MESSAGE: {e}"
            )
            return False

    @classmethod
    def get_bitrate(cls, input_file):
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_format',
                '-print_format', 'json',
                input_file
            ]
            result = cls.run_subprocess_with_flags(
                cmd,
                capture_output=True,
                text=True
            )
            metadata = json.loads(result.stdout)
            original_bitrate = int(metadata["format"]["bit_rate"])
            new_bitrate = ((original_bitrate // 5 + 99999) // 100000) * 100
            return f"{new_bitrate}K"
        except Exception as e:
            cls.LOGGER.error(
                f"Error while calculating bitrate for video:{input_file}. ERROR MESSAGE: {e}"
            )
            raise e

    @classmethod
    def is_codec_available(cls, codec):
        """Check if the specified codec is available on the system."""
        try:
            ffmpeg.input("dummy").output("dummy.mp4", vcodec=codec).global_args(
                "-loglevel", "error"
            ).compile()
            return True
        except ffmpeg.Error as e:
            cls.LOGGER.error(
                f"Error while detecting CODEC:{codec}. ERROR MESSAGE: {e.stderr.decode()}"
            )
            return False

    @classmethod
    def select_best_codec(cls):
        """Select the best available codec."""
        for codec in VIDEO_CODECS:
            if cls.is_codec_available(codec):
                return codec
        raise RuntimeError("No supported video codec is available.")

    @classmethod
    def compress_video_qsv(cls, input_file, output_file, bitrate, framerate=FRAMERATE):
        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-b:v', bitrate,
                '-vcodec', 'h264_qsv',
                '-r', str(framerate),
                '-metadata', 'comment=compressed',
                '-preset', 'medium',
                '-loglevel', 'error',
                output_file
            ]
            cls.run_subprocess_with_flags(
                cmd,
                capture_output=True,
                check=True
            )
            cls.LOGGER.info(f"Compressed video: {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            cls.LOGGER.error(
                f"An error occurred while encoding: {input_file}. ERROR MESSAGE: {e.stderr.decode()}"
            )

    @classmethod
    def compress_video_cpu(cls, input_file, output_file, bitrate, framerate=FRAMERATE):
        try:
            cmd = [
                'ffmpeg',
                '-i', input_file,
                '-b:v', bitrate,
                '-vcodec', 'libx264',  # CPU-based compression codec
                '-r', str(framerate),
                '-metadata', 'comment=compressed',
                '-loglevel', 'error',  # Suppress info, show only errors
                output_file
            ]
            cls.run_subprocess_with_flags(
                cmd,
                capture_output=True,
                check=True
            )
            cls.LOGGER.info(f"Compressed video: {input_file} to {output_file}")
        except subprocess.CalledProcessError as e:
            cls.LOGGER.error(
                f"An error occurred while encoding: {input_file}. ERROR MESSAGE: {e.stderr.decode()}"
            )

    @classmethod
    def compress_video(
        cls, input_file, output_file, bitrate, video_codec, framerate=FRAMERATE
    ):
        if video_codec == "h264_qsv":
            cls.compress_video_qsv(input_file, output_file, bitrate, framerate)
        else:
            cls.compress_video_cpu(input_file, output_file, bitrate, framerate)

    @classmethod
    def get_video_files(cls, input_directory):
        """Get a list of video files in the specified directory."""
        video_files = []
        for root, _, files in os.walk(input_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in VIDEO_FILETYPES):
                    if not cls.is_video_processed(os.path.join(root, file)):
                        video_files.append(os.path.join(root, file))
                    else:
                        cls.LOGGER.info(
                            f"Skipping video:{os.path.join(root, file)} as it is already processed"
                        )
        return video_files

    @classmethod
    def compress_videos_in_directory(
        cls, input_directory, output_directory, progress_callback=None, framerate=30
    ):
        setup_logging(output_directory)
        cls.LOGGER = logging.getLogger(__name__)

        cls.LOGGER.info(f"Started compressing videos in directory:{input_directory}")

        # Select the best available codec
        video_codec = cls.select_best_codec()

        # Gather video files
        video_files = cls.get_video_files(input_directory)

        # Calculate total size of all files
        total_size = sum(os.path.getsize(f) for f in video_files)
        processed_size = 0

        # Process each video file
        total_files = len(video_files)
        for idx, input_file in enumerate(video_files, start=0):
            try:
                # Update progress
                if progress_callback:
                    progress = processed_size / total_size if total_size > 0 else 0
                    progress_callback(progress, input_file, idx, total_files)

                # Calculate output file path
                relative_path = os.path.relpath(input_file, input_directory)
                output_file = os.path.join(output_directory, relative_path)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Calculate bitrate
                bitrate = cls.get_bitrate(input_file)

                # Compress video
                cls.compress_video(
                    input_file, output_file, bitrate, video_codec, framerate
                )

                # Update processed size
                processed_size += os.path.getsize(input_file)

            except Exception as e:
                cls.LOGGER.error(
                    f"Uncaught error occurred while compressing:{input_file}. ERROR MESSAGE: {str(e)}"
                )

        if progress_callback:
            progress_callback(1, "", total_files, total_files)
        cls.LOGGER.info(f"Finished compressing videos in directory:{input_directory}")
