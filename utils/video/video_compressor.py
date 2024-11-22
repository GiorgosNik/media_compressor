import ffmpeg
import os
import tqdm
from datetime import datetime
import yaml

class VideoCompressor:
    # Conversion parameters
    VIDEO_CODEC = "libx264"     # Video codec
    FRAMERATE = 29.97           # Frame rate
    
    # Path to the YAML file
    yaml_file = "config.yaml"

    # Load video file extensions from the YAML file
    with open(yaml_file, 'r') as file:
        yaml_data = yaml.safe_load(file)
        VIDEO_FILETYPES = yaml_data.get('video_filetypes', [])

    def __get_bitrate(self, input_file):
        """Get the original bitrate of a video and return 1/5th of it, rounded up to the nearest 100Kbps."""
        probe = ffmpeg.probe(input_file)
        original_bitrate = int(probe['format']['bit_rate'])
        new_bitrate = ((original_bitrate // 5 + 99999) // 100000) * 100
        return f"{new_bitrate}K"

    def __compress_video(self, input_file, output_file, bitrate, video_codec=VIDEO_CODEC, framerate=FRAMERATE):
        try:
            (
                ffmpeg
                .input(input_file)
                .output(
                    output_file,
                    video_bitrate=bitrate,
                    vcodec=video_codec,
                    r=framerate
                )
                .global_args('-loglevel', 'error')  # Suppress info, show only errors
                .run()
            )
            print(f"Compressed file saved as {output_file}")
        except ffmpeg.Error as e:
            print(f"An error occurred: {e.stderr.decode()}")

    def compress_videos_in_directory(self, input_directory, video_codec=VIDEO_CODEC, framerate=FRAMERATE):
        # Create a timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_directory = f"./output_{timestamp}"
        os.makedirs(output_directory, exist_ok=True)
        
        # Get the list of video files
        video_files = [f for f in os.listdir(input_directory) if any(f.lower().endswith(ext) for ext in self.VIDEO_FILETYPES)]        
        
        # Set up the progress bar
        with tqdm.tqdm(total=len(video_files), desc="Compressing Videos", unit="file") as pbar:
            for filename in video_files:
                input_file = os.path.join(input_directory, filename)
                output_file = os.path.join(output_directory, filename)
                
                # Calculate the dynamic bitrate
                bitrate = self.__get_bitrate(input_file)
                
                # Update progress bar with current video name
                pbar.set_postfix({"Current Video": filename, "Bitrate": bitrate})
                
                # Compress the video
                self.__compress_video(input_file, output_file, bitrate, video_codec, framerate)
                
                # Update progress bar
                pbar.update(1)