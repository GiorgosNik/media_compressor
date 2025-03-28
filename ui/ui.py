import ctypes
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import StringVar, filedialog
from threading import Thread
import os
from utils.handler.handler import Handler
from datetime import datetime
import time
import webbrowser
from tkinterdnd2 import TkinterDnD, DND_ALL


try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# Create the main application class
class CompressorApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.title("GEP Media Compressor")
        self.iconbitmap("./assets/ges.ico")
        self.geometry("500x200")
        self.running = False
        self.TkdndVersion = TkinterDnD._require(self)
        self.thread = None

        # Define constants
        self.SELECT_DIRECTORY_TEXT = "Select a directory"

        # Tracking time and progress
        self.start_time = None
        self.total_files = 0

        # UI widget storage
        self.widgets = {}
        self.drop_target_register(DND_ALL)
        self.dnd_bind("<<Drop>>", self.get_path)
        self.setup_initial_ui()

    def get_path(self, event):
        dropped_location = event.data.replace("{","").replace("}", "")
        if not self.running and (os.path.isdir(dropped_location) or os.path.isfile(dropped_location)):
            self.clear_placeholder(None)
            self.directory = dropped_location
            self.directory_string_var.set(self.directory)

    def open_output_directory(self):
        # Open the directory in the file explorer
        if os.name == "nt":  # Windows
            os.startfile(self.directory)
        elif os.name == "posix":  # macOS/Linux
            subprocess.Popen(
                ["open", self.directory]
                if "darwin" in os.sys.platform
                else ["xdg-open", self.directory]
            )

    def setup_initial_ui(self):
        self.clear_ui()

        self.directory_string_var = StringVar()
        self.directory_string_var.set(self.SELECT_DIRECTORY_TEXT)
        self.directory_string_var.trace_add("write", lambda *args: self.on_text_change())
        
        self.directory = ""

        self.widgets["dir_input"] = ctk.CTkEntry(
            self,
            width=400,
            textvariable=self.directory_string_var,
        )
        self.widgets["dir_input"].pack(pady=20)

        # Bind events for placeholder handling
        self.widgets["dir_input"].bind("<FocusIn>", self.clear_placeholder)
        self.widgets["dir_input"].bind("<FocusOut>", self.restore_placeholder)
        self.widgets["dir_input"].configure(text_color="grey")

        # Bind global click event to detect outside clicks
        self.bind_all("<Button-1>", self.on_global_click)

        self.widgets["button_frame"] = ctk.CTkFrame(self, fg_color="transparent")
        self.widgets["button_frame"].pack(pady=10)

        self.widgets["select_button"] = ctk.CTkButton(
            self.widgets["button_frame"],
            text="Select Directory",
            command=self.select_directory,
        )
        self.widgets["select_button"].pack(side="left", padx=10)
        
        self.widgets["file_select_button"] = ctk.CTkButton(
            self.widgets["button_frame"],
            text="Select File",
            command=self.select_file,
        )
        self.widgets["file_select_button"].pack(side="left", padx=10)

        self.widgets["start_button"] = ctk.CTkButton(
            self.widgets["button_frame"],
            text="Start Compression",
            command=self.start_application,
        )
        self.widgets["start_button"].pack(side="left", padx=10)

        self.widgets["help_button"] = ctk.CTkButton(
            self,
            text="?",
            width=30,
            height=30,
            corner_radius=50,
            command=self.show_help_message,
        )
        self.widgets["help_button"].place(x=460, y=18)

        self.process_video = True
        self.process_image = True
        self.convert_incompatible = True

        self.widgets["checkbox_frame"] = ctk.CTkFrame(self, fg_color="transparent")
        self.widgets["checkbox_frame"].pack(pady=20)

        self.widgets["video_checkbox"] = ctk.CTkCheckBox(
            self.widgets["checkbox_frame"],
            text="Process Video",
            command=lambda: setattr(
                self, "process_video", self.widgets["video_checkbox"].get()
            ),
        )
        self.widgets["video_checkbox"].pack(side="left", padx=20)
        self.widgets["video_checkbox"].select()

        self.widgets["image_checkbox"] = ctk.CTkCheckBox(
            self.widgets["checkbox_frame"],
            text="Process Image",
            command=lambda: setattr(
                self, "process_image", self.widgets["image_checkbox"].get()
            ),
        )
        self.widgets["image_checkbox"].pack(side="left", padx=20)
        self.widgets["image_checkbox"].select()

        self.widgets["convert_incompatible_checkbox"] = ctk.CTkCheckBox(
            self.widgets["checkbox_frame"],
            text="Convert Incompatible \n formats to MP4",
            command=lambda: setattr(
                self, "convert_incompatible", self.widgets["convert_incompatible_checkbox"].get()
            ),
        )
        self.widgets["convert_incompatible_checkbox"].pack(side="left", padx=20)
        self.widgets["convert_incompatible_checkbox"].select()

    def clear_placeholder(self, event):
        if self.directory_string_var.get() == self.SELECT_DIRECTORY_TEXT:
            self.directory_string_var.set("")
            self.widgets["dir_input"].configure(text_color="white")

    def restore_placeholder(self, event):
        if not self.directory_string_var.get().strip():
            self.directory_string_var.set(self.SELECT_DIRECTORY_TEXT)
            self.focus()
            self.widgets["dir_input"].configure(text_color="grey")

    def on_global_click(self, event):
        widget = event.widget
        if widget != self.widgets["dir_input"]:
            self.restore_placeholder(None)

    def clear_ui(self):
        """Forget all widgets."""
        for widget in self.widgets.values():
            widget.pack_forget()

    def on_text_change(self, *args):
        self.directory = self.directory_string_var.get()

    def select_directory(self):
        # Open directory selection dialog
        self.clear_placeholder(None)
        directory = filedialog.askdirectory()
        if directory:
            self.widgets["dir_input"].delete(0, ctk.END)
            self.widgets["dir_input"].insert(0, directory)
            self.directory = directory
            
    def select_file(self):
        # Open file selection dialog
        self.clear_placeholder(None)
        given_file = filedialog.askopenfilename()
        if given_file:
            self.widgets["dir_input"].delete(0, ctk.END)
            self.widgets["dir_input"].insert(0, given_file)
            self.given_file = given_file

    def show_help_message(self):
        option = CTkMessagebox(
            title="GEP Media Compressor Help",
            message=(
                "- Select Directory: Choose a folder with videos.\n"
                "- Start Application: Begin compressing the videos.\n"
                "- Stop Operation: Cancel the compression process.\n\n"
            ),
            wraplength=280,
            option_1="Contact Developer",
            option_2="Get Updates",
            option_3="View README",
        ).get()
        if option == "Contact Developer":
            webbrowser.open(
                "mailto:giorgosnl17@gmail.com?subject=GEP Compressor: Request for Support"
            )
        elif option == "Get Updates":
            webbrowser.open("https://github.com/GiorgosNik/media_compressor/releases")
        elif option == "View README":
            webbrowser.open(
                "https://github.com/GiorgosNik/media_compressor/blob/main/README.md"
            )

    def start_application(self):
        if not self.directory:
            CTkMessagebox(
                title="Error",
                message="Please provide a directory before starting.",
                icon="cancel",
            ).get()
            return
        if not (os.path.isdir(self.directory) or os.path.isfile(self.directory)):
            CTkMessagebox(
                title="Error",
                message="The selected directory is not valid. Please select a valid directory.",
                icon="cancel",
            ).get()
            return

        # Clear the initial UI
        self.running = True
        self.setup_running_ui()

    def setup_running_ui(self):
        # Forget all widgets
        self.clear_ui()

        # Progress bar
        self.widgets["progress_bar"] = ctk.CTkProgressBar(
            self, orientation="horizontal", width=400
        )
        self.widgets["progress_bar"].pack(pady=10)
        self.widgets["progress_bar"].set(0)

        # Progress details
        self.widgets["elapsed_time_label"] = ctk.CTkLabel(
            self, text="Elapsed Time: 00:00:00"
        )
        self.widgets["elapsed_time_label"].pack()

        self.widgets["eta_label"] = ctk.CTkLabel(self, text="ETA: --:--:--")
        self.widgets["eta_label"].pack()

        self.widgets["current_file_label"] = ctk.CTkLabel(
            self, text="Current File: None"
        )
        self.widgets["current_file_label"].pack()

        self.widgets["file_count_label"] = ctk.CTkLabel(self, text="Processed: 0/0")
        self.widgets["file_count_label"].pack()

        # Stop button
        self.widgets["stop_button"] = ctk.CTkButton(
            self, text="Stop Compression", command=self.stop_operation
        )
        self.widgets["stop_button"].pack(pady=10)

        # Start compression in a separate thread
        self.thread = Thread(target=self.compress_media, args=(self.directory,))
        self.thread.start()

    def compress_media(self, input_directory):
        try:
            self.start_time = datetime.now()  # Record the start time
            self.eta_seconds_remaining = None  # Initialize ETA countdown
            self.updater_running = True  # Control for the update thread

            def time_updater():
                """Thread to update elapsed time and countdown ETA every second."""
                while self.updater_running:
                    elapsed_time = datetime.now() - self.start_time

                    # Update elapsed time label
                    self.widgets["elapsed_time_label"].configure(
                        text=f"Elapsed Time: {str(elapsed_time).split('.')[0]}"
                    )

                    # Update ETA countdown if applicable
                    if self.eta_seconds_remaining and self.eta_seconds_remaining > 0:
                        self.eta_seconds_remaining -= 1
                        mins, secs = divmod(self.eta_seconds_remaining, 60)
                        hours, mins = divmod(mins, 60)
                        self.widgets["eta_label"].configure(
                            text=f"ETA: {hours:02}:{mins:02}:{secs:02}"
                        )
                    elif self.eta_seconds_remaining == 0:
                        self.widgets["eta_label"].configure(text="ETA: 00:00:00")

                    time.sleep(1)

            # Start the updater thread
            Thread(target=time_updater, daemon=True).start()

            def update_progress(progress_ratio, current_file, file_index, total_files):
                """Update the progress bar, labels, and estimate the ETA."""
                self.widgets["progress_bar"].set(progress_ratio)

                # Estimate ETA and update countdown tracker
                if progress_ratio > 0 and progress_ratio != 1:
                    elapsed_time = datetime.now() - self.start_time
                    estimated_total_time = elapsed_time / progress_ratio
                    eta = estimated_total_time - elapsed_time
                    self.eta_seconds_remaining = int(eta.total_seconds())
                elif progress_ratio == 1:
                    self.eta_seconds_remaining = 0

                # Update current file and progress count
                self.widgets["current_file_label"].configure(
                    text=f"Current File: {os.path.basename(current_file)}"
                )
                self.widgets["file_count_label"].configure(
                    text=f"Processed: {file_index}/{total_files}"
                )

            # Call the compression handler with the callback
            original_size, compressed_size, = Handler.start_compression(
                input_directory=input_directory,
                process_video=self.process_video,
                process_image=self.process_image,
                convert_incompatible=self.convert_incompatible,
                progress_callback=lambda progress_ratio, current_file, file_index, total_files: update_progress(
                    progress_ratio, current_file, file_index, total_files
                ),
            )
            
            self.original_size = original_size
            self.compressed_size = compressed_size

            # Notify the user upon successful completion
            if self.running:
                self.show_operation_completed_message()
                self.running = False

        except RuntimeError as e:
            # Notify the user of any errors encountered during compression
            CTkMessagebox(
                title="Runtime Error", message=f"Error: {str(e)}", icon="cancel"
            ).get()

        finally:
            self.updater_running = False
            Handler.cleanup_logging()
            self.setup_initial_ui()

    def show_operation_completed_message(self):
        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024 or unit == 'GB':
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024
        
        original = format_size(self.original_size)
        compressed = format_size(self.compressed_size)
        savings = round((1 - (self.compressed_size / self.original_size)) * 100) if self.original_size > 0 else 0
        
        message = (f"Operation Completed Successfully!\n\n"
                f"Original size: {original}\n"
                f"Compressed size: {compressed}\n"
                f"Space saved: {savings}%")
        
        option = CTkMessagebox(
            title="Operation Completed",
            message=message,
            icon="check",
            option_1="OK",
            option_2="Open Directory",
            width=500
        ).get()
        
        if option == "Open Directory":
            self.open_output_directory()

    def stop_operation(self):
        if not self.thread or self.thread.is_alive():
            return
        tid = ctypes.c_long(self.thread.ident)
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
            tid, ctypes.py_object(SystemExit)
        )
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
            raise RuntimeError("Failed to kill thread")
        self.running = False
        self.eta_updater_running = False  # Stop the countdown
        CTkMessagebox(message="The operation has been stopped.").get()
        self.setup_initial_ui()
