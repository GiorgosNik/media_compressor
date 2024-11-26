import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import StringVar, filedialog
from threading import Thread
import os
from utils.handler.handler import Handler
from datetime import datetime
import time

# Create the main application class
class CompressorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("GEP Media Compressor")
        self.iconbitmap('./assets/ges.ico')
        self.geometry("500x200")
        self.running = False

        # Tracking time and progress
        self.start_time = None
        self.total_files = 0

        # UI widget storage
        self.widgets = {}

        # Initial UI setup
        self.setup_initial_ui()

    def setup_initial_ui(self):
        # Forget all currently packed widgets
        self.clear_ui()

        # Directory input field
        self.directory_string_var = StringVar()
        self.directory_string_var.trace_add("write", self.on_text_change)
        
        self.widgets['dir_input'] = ctk.CTkEntry(
            self, width=400, placeholder_text="Select a directory", textvariable=self.directory_string_var
        )
        self.widgets['dir_input'].pack(pady=20)
        
        # Frame to hold the buttons side by side
        self.widgets['button_frame'] = ctk.CTkFrame(self)
        self.widgets['button_frame'].pack(pady=10)

        # Buttons
        self.widgets['select_button'] = ctk.CTkButton(
            self.widgets['button_frame'], text="Select Directory", command=self.select_directory
        )
        self.widgets['select_button'].pack(side="left", padx=10)

        self.widgets['start_button'] = ctk.CTkButton(
            self.widgets['button_frame'], text="Start Application", command=self.start_application
        )
        self.widgets['start_button'].pack(side="left", padx=10)
    
    def clear_ui(self):
        """Forget all widgets."""
        for widget in self.widgets.values():
            widget.pack_forget()

    def on_text_change(self, *args):
        self.directory = self.widgets['dir_input'].get()

    def select_directory(self):
        # Open directory selection dialog
        directory = filedialog.askdirectory()
        if directory:
            self.widgets['dir_input'].delete(0, ctk.END)
            self.widgets['dir_input'].insert(0, directory)
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
        # Forget all widgets
        self.clear_ui()

        # Progress bar
        self.widgets['progress_bar'] = ctk.CTkProgressBar(self, orientation="horizontal", width=400)
        self.widgets['progress_bar'].pack(pady=10)
        self.widgets['progress_bar'].set(0)

        # Progress details
        self.widgets['elapsed_time_label'] = ctk.CTkLabel(self, text="Elapsed Time: 00:00:00")
        self.widgets['elapsed_time_label'].pack()

        self.widgets['eta_label'] = ctk.CTkLabel(self, text="ETA: --:--:--")
        self.widgets['eta_label'].pack()

        self.widgets['current_file_label'] = ctk.CTkLabel(self, text="Current File: None")
        self.widgets['current_file_label'].pack()

        self.widgets['file_count_label'] = ctk.CTkLabel(self, text="Processed: 0/0")
        self.widgets['file_count_label'].pack()

        # Stop button
        self.widgets['stop_button'] = ctk.CTkButton(self, text="Stop Operation", command=self.stop_operation)
        self.widgets['stop_button'].pack(pady=10)

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
        try:
            self.start_time = datetime.now()  # Record the start time
            self.eta_seconds_remaining = None  # Initialize ETA countdown
            self.updater_running = True  # Control for the update thread

            def time_updater():
                """Thread to update elapsed time and countdown ETA every second."""
                while self.updater_running:
                    elapsed_time = datetime.now() - self.start_time

                    # Update elapsed time label
                    self.widgets['elapsed_time_label'].configure(
                        text=f"Elapsed Time: {str(elapsed_time).split('.')[0]}"
                    )

                    # Update ETA countdown if applicable
                    if self.eta_seconds_remaining and self.eta_seconds_remaining > 0:
                        self.eta_seconds_remaining -= 1
                        mins, secs = divmod(self.eta_seconds_remaining, 60)
                        hours, mins = divmod(mins, 60)
                        self.widgets['eta_label'].configure(
                            text=f"ETA: {hours:02}:{mins:02}:{secs:02}"
                        )
                    elif self.eta_seconds_remaining == 0:
                        self.widgets['eta_label'].configure(text="ETA: 00:00:00")

                    time.sleep(1)

            # Start the updater thread
            Thread(target=time_updater, daemon=True).start()

            def update_progress(progress_ratio, current_file, file_index, total_files):
                """Update the progress bar, labels, and estimate the ETA."""
                self.widgets['progress_bar'].set(progress_ratio)

                # Estimate ETA and update countdown tracker
                if progress_ratio > 0 and progress_ratio != 1:
                    elapsed_time = datetime.now() - self.start_time
                    estimated_total_time = elapsed_time / progress_ratio
                    eta = estimated_total_time - elapsed_time
                    self.eta_seconds_remaining = int(eta.total_seconds())
                elif progress_ratio == 1:
                    self.eta_seconds_remaining = 0

                # Update current file and progress count
                self.widgets['current_file_label'].configure(
                    text=f"Current File: {os.path.basename(current_file)}"
                )
                self.widgets['file_count_label'].configure(
                    text=f"Processed: {file_index}/{total_files}"
                )

            # Call the compression handler with the callback
            Handler.start_compression(
                input_directory=input_directory,
                progress_callback=lambda progress_ratio, current_file, file_index, total_files: update_progress(
                    progress_ratio, current_file, file_index, total_files
                ),
            )

            # Notify the user upon successful completion
            if self.running:  # Ensure the operation was not stopped
                CTkMessagebox(
                    title="Operation Completed", message="Operation Completed Successfully!", icon="check"
                ).get()

        except RuntimeError as e:
            # Notify the user of any errors encountered during compression
            CTkMessagebox(
                title="Runtime Error", message=f"Error: {str(e)}", icon="cancel"
            ).get()

        finally:
            # Stop the updater thread and reset the UI to its initial state
            self.updater_running = False
            self.setup_initial_ui()

    def stop_operation(self):
        # Stop the running process
        self.running = False
        self.eta_updater_running = False  # Stop the countdown
        CTkMessagebox(message="The operation has been stopped.").get()
        self.setup_initial_ui()
