import ffmpeg
import os
from datetime import datetime
from utils.video.config import VIDEO_FILETYPES
from utils.video.config import VIDEO_CODECS

class VideoCompressor:
    FRAMERATE = 29.97
    
    @classmethod
    def is_video_proccessed(cls, file_path):
        try:
        # Get the metadata using ffprobe
            vid = ffmpeg.probe(file_path)['format']['tags']
            if vid.get('comment') == 'compressed':
                return True
            else:
                return False
        except ffmpeg.Error as e:
            print(f"Error checking metadata: {e.stderr.decode()}")
            return False

    @classmethod
    def __get_bitrate(cls, input_file):
        """Get the original bitrate of a video and return 1/5th of it, rounded up to the nearest 100Kbps."""
        probe = ffmpeg.probe(input_file)
        original_bitrate = int(probe['format']['bit_rate'])
        new_bitrate = ((original_bitrate // 5 + 99999) // 100000) * 100
        return f"{new_bitrate}K"

    @classmethod
    def __is_codec_available(cls, codec):
        """Check if the specified codec is available on the system."""
        try:
            ffmpeg.input('dummy').output('dummy.mp4', vcodec=codec).global_args('-loglevel', 'error').compile()
            return True
        except ffmpeg.Error:
            return False
    
    @classmethod
    def select_best_codec(cls):
        """Select the best available codec."""
        for codec in VIDEO_CODECS:
            if cls.__is_codec_available(codec):
                return codec
        raise RuntimeError("No supported video codec is available.")

    @classmethod
    def __compress_video_qsv(cls, input_file, output_file, bitrate, framerate=FRAMERATE):
        try:
                (
                    ffmpeg
                    .input(input_file)
                    .output(
                        output_file,
                        video_bitrate=bitrate,
                        vcodec="h264_qsv",
                        r=framerate,
                        metadata = "comment=compressed",
                        # QSV-specific options
                        preset="medium",  # Adjust the preset to balance speed and quality
                    )
                    .global_args('-loglevel', 'error')  # Suppress info, show only errors
                    .run()
                )
                print(f"Compressed file saved as {output_file}")
        except ffmpeg.Error as e:
            print(f"An error occurred: {e.stderr.decode()}")
            
    @classmethod
    def __compress_video_cpu(cls, input_file, output_file, bitrate, framerate=FRAMERATE):
        try:
                (
                    ffmpeg
                    .input(input_file)
                    .output(
                        output_file,
                        video_bitrate=bitrate,
                        vcodec="h264_qsv",
                        r=framerate,
                        metadata = "comment=compressed",
                    )
                    .global_args('-loglevel', 'error')  # Suppress info, show only errors
                    .run()
                )
                print(f"Compressed file saved as {output_file}")
        except ffmpeg.Error as e:
            print(f"An error occurred: {e.stderr.decode()}")

    @classmethod
    def __compress_video(cls, input_file, output_file, bitrate, video_codec, framerate=FRAMERATE):
        if video_codec == "h264_qsv":
            cls.__compress_video_qsv(input_file, output_file, bitrate, framerate)
        else:
            cls.__compress_video_cpu(input_file, output_file, bitrate, framerate)
            

    @classmethod
    def compress_videos_in_directory(cls, input_directory, output_directory, progress_callback=None, framerate=30):
        # Select the best available codec
        video_codec = cls.select_best_codec()

        # Gather video files
        video_files = []
        for root, _, files in os.walk(input_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in VIDEO_FILETYPES):
                    if(not cls.is_video_proccessed(os.path.join(root, file))):
                        video_files.append(os.path.join(root, file))

        # Process each video file
        total_files = len(video_files)
        for idx, input_file in enumerate(video_files, start=0):
            # Update progress
            if progress_callback:
                progress_callback(idx / total_files, input_file, idx, total_files)
            
            # Calculate output file path
            relative_path = os.path.relpath(input_file, input_directory)
            output_file = os.path.join(output_directory, relative_path)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Calculate bitrate
            bitrate = cls.__get_bitrate(input_file)

            # Compress video
            cls.__compress_video(input_file, output_file, bitrate, video_codec, framerate)
            
            
        if progress_callback:
                progress_callback(1, "", total_files, total_files)
