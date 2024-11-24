# GEP Media Compressor

GEP Media Compressor is a Python-based application designed to compress video files in a specified directory. The application uses `ffmpeg` for video compression and provides a graphical user interface (GUI) built with `customtkinter`.

## Features

- Compress video files in a specified directory.
- Automatically select the best available codec for compression.
- Display progress, elapsed time, and estimated time of arrival (ETA) during compression.
- Option to stop the compression process at any time.
- Logging of all operations and errors.

## Requirements

- Python 3.6+
- `ffmpeg` installed and available in the system PATH.
- Required Python packages:
    - `customtkinter`
    - `ffmpeg-python`
    - `CTkMessagebox`

## Installation

1. Clone the repository:
        ```sh
        git clone https://github.com/yourusername/media-compressor.git
        cd media-compressor
        ```

2. Install the required Python packages:
        ```sh
        pip install -r requirements.txt
        ```

3. Ensure `ffmpeg` is installed and available in your system PATH. You can download it from [ffmpeg.org](https://ffmpeg.org/download.html).

## Usage

1. Run the application:
        ```sh
        python main.py
        ```

2. Use the GUI to select the directory containing the video files you want to compress.

3. Click "Start Application" to begin the compression process.

4. Monitor the progress, elapsed time, and ETA in the GUI.

5. Optionally, click "Stop Operation" to halt the compression process.

## Project Structure

- `main.py`: Entry point of the application.
- `ui/ui.py`: Contains the GUI implementation.
- `utils/video/video_compressor.py`: Contains the video compression logic.
- `utils/handler/handler.py`: Handles the compression process.
- `utils/logging/logging.py`: Sets up logging configuration.
- `utils/video/config.py`: Configuration for video file types and codecs.
- `README.md`: Project documentation.
- `.gitignore`: Specifies files and directories to be ignored by Git.
- `TODO`: List of tasks and improvements for the project.

## Logging

Logs are saved to `app.log` in the project directory. The log includes information about the compression process, errors, and other relevant events.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgements

- [ffmpeg](https://ffmpeg.org/) for the powerful multimedia framework.
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern and customizable GUI toolkit.
- [CTkMessagebox](https://github.com/TomSchimansky/CTkMessagebox) for the message box implementation.
