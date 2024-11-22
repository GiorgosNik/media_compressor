import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import StringVar, filedialog
from threading import Thread
import time
import os
from utils.video.video_compressor import VideoCompressor

# Create the main application class
class CompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GEP Media Compressor")
        self.iconbitmap('./assets/ges.ico')
        self.geometry("500x200")
        self.directory = None
        self.running = False

        # Initial UI setup
        self.setup_initial_ui()

    def setup_initial_ui(self):
        # Clear the window
        for widget in self.winfo_children():
            widget.destroy()

        # Directory input field
        self.directory_string_var = StringVar()
        self.directory_string_var.trace_add("write", self.on_text_change)
        
        self.dir_input = ctk.CTkEntry(self, width=400, placeholder_text="Select a directory", textvariable=self.directory_string_var)
        self.dir_input.pack(pady=20)
        
        # Frame to hold the buttons side by side
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(pady=10)

        # Buttons
        self.select_button = ctk.CTkButton(button_frame, text="Select Directory", command=self.select_directory)
        self.select_button.pack(side="left", padx=10)

        self.start_button = ctk.CTkButton(button_frame, text="Start Application", command=self.start_application)
        self.start_button.pack(side="left", padx=10)
    
    def on_text_change(self, *args):
        self.directory =self.dir_input.get()

    def select_directory(self):
        # Open directory selection dialog
        directory = filedialog.askdirectory()
        if directory:
            self.dir_input.delete(0, ctk.END)
            self.dir_input.insert(0, directory)
            self.directory = directory

    def start_application(self):
        if not self.directory:
            CTkMessagebox(title="Error", message="Please select a directory before starting.", icon="cancel").get()
            return
        
        if not os.path.isdir(self.directory):
            CTkMessagebox(title="Error", message="The selected directory is not valid. Please select a valid directory.", icon="cancel").get()
            return

        # Clear the initial UI
        self.running = True
        self.setup_running_ui()

        # Start the application process in a separate thread
        Thread(target=self.run_application).start()

    def setup_running_ui(self):
        # Clear the window
        for widget in self.winfo_children():
            widget.destroy()

        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self, orientation="horizontal", width=400)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)

        # Stop button
        self.stop_button = ctk.CTkButton(self, text="Stop Operation", command=self.stop_operation)
        self.stop_button.pack(pady=10)

    def run_application(self):
        if not self.directory:
            CTkMessagebox(title="Error", message="Please select a directory before starting.", icon="cancel").get()
            return

        if not os.path.isdir(self.directory):
            CTkMessagebox(title="Error", message="The selected directory is not valid.", icon="cancel").get()
            return

        self.running = True
        self.setup_running_ui()

        # Start compression in a separate thread
        Thread(target=self.compress_videos, args=(self.directory,)).start()


    def compress_videos(self, input_directory):
        """
        Compress videos in the selected directory.
        
        Args:
            input_directory (str): Path to the directory containing videos to compress.
        """
        try:
            # Define a callback to update the progress bar in the UI
            def update_progress(progress_ratio):
                self.progress_bar.set(progress_ratio)

            # Call the VideoCompressor method
            VideoCompressor.compress_videos_in_directory(
                input_directory=input_directory,
                progress_callback=update_progress  # Pass the callback function
            )

            # Notify the user upon successful completion
            if self.running:  # Ensure the operation was not stopped
                CTkMessagebox(title="Operation Completed" ,message="Operation Completed Successfully!", icon="check").get()

        except RuntimeError as e:
            # Notify the user of any errors encountered during compression
            CTkMessagebox(title="Runtime Error", message=f"Error: {str(e)}", icon="cancel").get()

        finally:
            # Reset the UI to its initial state, regardless of success or failure
            self.setup_initial_ui()

            
    def stop_operation(self):
        # Stop the running process
        self.running = False
        CTkMessagebox(message="The operation has been stopped.").get()
        self.setup_initial_ui()