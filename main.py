import customtkinter as ctk
from ui.ui import CompressorApp
from utils.video.video_compressor import VideoCompressor

# Run the application
if __name__ == "__main__":
    # ctk.set_appearance_mode("Dark")  
    # ctk.set_default_color_theme("blue")

    # app = CompressorApp()
    # app.mainloop()
    
    VideoCompressor.compress_videos_in_directory("./")