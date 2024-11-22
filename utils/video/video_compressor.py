import ffmpeg
import os
import tqdm
from datetime import datetime
from utils.video.config import VIDEO_FILETYPES
from utils.video.config import VIDEO_CODECS

class VideoCompressor:
    FRAMERATE = 29.97

    @classmethod
    def __get_bitrate(self, input_file):
        """Get the original bitrate of a video and return 1/5th of it, rounded up to the nearest 100Kbps."""
        probe = ffmpeg.probe(input_file)
        original_bitrate = int(probe['format']['bit_rate'])
        new_bitrate = ((original_bitrate // 5 + 99999) // 100000) * 100
        return f"{new_bitrate}K"

    @classmethod
    def __is_codec_available(self, codec):
        """Check if the specified codec is available on the system."""
        try:
            ffmpeg.input('dummy').output('dummy.mp4', vcodec=codec).global_args('-loglevel', 'error').compile()
            return True
        except ffmpeg.Error:
            return False
    
    @classmethod
    def select_best_codec(self):
        """Select the best available codec."""
        for codec in VIDEO_CODECS:
            if self.__is_codec_available(codec):
                return codec
        else:
            raise RuntimeError("No supported video codec is available.")

    @classmethod
    def __compress_video(self, input_file, output_file, bitrate, video_codec, framerate=FRAMERATE):
        try:
            (
                ffmpeg
                .input(input_file)
                .output(
                    output_file,
                    video_bitrate=bitrate,
                    vcodec=video_codec,
                    r=framerate,
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
    def compress_videos_in_directory(cls, input_directory, framerate=30, progress_callback=None):
        # Select the best available codec
        video_codec = cls.select_best_codec()

        # Create a timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_directory = f"./output_{timestamp}"
        os.makedirs(output_directory, exist_ok=True)

        # Gather video files
        video_files = []
        for root, _, files in os.walk(input_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in VIDEO_FILETYPES):
                    video_files.append(os.path.join(root, file))

        if not video_files:
            raise RuntimeError("No video files found in the selected directory.")

        # Process each video file
        total_files = len(video_files)
        for idx, input_file in enumerate(video_files, start=0):
            # Update progress
            if progress_callback:
                progress_callback(idx / total_files, input_file, idx)
            
            # Calculate output file path
            relative_path = os.path.relpath(input_file, input_directory)
            output_file = os.path.join(output_directory, relative_path)
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

            # Calculate bitrate
            bitrate = cls.__get_bitrate(input_file)

            # Compress video
            cls.__compress_video(input_file, output_file, bitrate, video_codec, framerate)

            

