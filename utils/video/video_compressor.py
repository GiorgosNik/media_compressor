import ffmpeg
import os
import tqdm
from datetime import datetime
from utils.video.config import video_filetypes

class VideoCompressor:
    # Conversion parameters
    VIDEO_CODEC = "libx264"     # Video codec
    FRAMERATE = 29.97           # Frame rate
    VIDEO_FILETYPES = video_filetypes

    @classmethod
    def __get_bitrate(self, input_file):
        """Get the original bitrate of a video and return 1/5th of it, rounded up to the nearest 100Kbps."""
        probe = ffmpeg.probe(input_file)
        original_bitrate = int(probe['format']['bit_rate'])
        new_bitrate = ((original_bitrate // 5 + 99999) // 100000) * 100
        return f"{new_bitrate}K"

    @classmethod
    def __compress_video(self, input_file, output_file, bitrate, video_codec=VIDEO_CODEC, framerate=FRAMERATE):
        try:
            (
                ffmpeg
                .input(input_file)
                .output(output_file, video_bitrate=bitrate, vcodec=video_codec, r=framerate)
                .global_args('-loglevel', 'error')  # Suppress info, show only errors
                .run()
            )
            print(f"Compressed file saved as {output_file}")
        except ffmpeg.Error as e:
            print(f"An error occurred: {e.stderr.decode()}")

    @classmethod
    def compress_videos_in_directory(self, input_directory, video_codec="h264", framerate=30):
        # Create a timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_directory = f"./output_{timestamp}"
        os.makedirs(output_directory, exist_ok=True)

        # Walk through all files and directories recursively
        video_files = []
        for root, _, files in os.walk(input_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.VIDEO_FILETYPES):
                    video_files.append(os.path.join(root, file))

        # Set up the progress bar
        with tqdm.tqdm(total=len(video_files), desc="Compressing Videos", unit="file") as pbar:
            for input_file in video_files:
                # Compute relative path to retain directory structure
                relative_path = os.path.relpath(input_file, input_directory)
                output_file = os.path.join(output_directory, relative_path)

                # Create necessary directories for the output file
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Calculate the dynamic bitrate
                bitrate = self.__get_bitrate(input_file)

                # Update progress bar with current video name
                pbar.set_postfix({"Current Video": os.path.basename(input_file), "Bitrate": bitrate})

                # Compress the video
                self.__compress_video(input_file, output_file, bitrate, video_codec, framerate)

                # Update progress bar
                pbar.update(1)