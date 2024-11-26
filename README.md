# GEP Media Compressor

GEP Media Compressor is a Python-based application designed to compress video and image files efficiently. It provides a user-friendly interface for selecting directories, monitoring progress, and handling errors during the compression process.

## Features

- **Video Compression**: Supports various video codecs including `h264_qsv` and CPU-based compression.
- **Image Compression**: Handles JPEG, PNG, and TIFF formats with metadata preservation.
- **Progress Tracking**: Displays elapsed time, estimated time of arrival (ETA), and current file being processed.
- **Error Handling**: Logs errors and provides user notifications for issues encountered during compression.
- **User Interface**: Built with `customtkinter` for a modern and responsive UI.

## Installation

### Prerequisites

- Python 3.12
- `ffmpeg` and `ffprobe` installed and available in the system PATH. Alternatively, they are available locally.

### Steps

1. Clone the repository:
        ```sh
        git clone https://github.com/GiorgosNik/media_compressor.git
        cd media_compressor
        ```

2. Install the required dependencies:
        ```sh
        pip install -r requirements.txt
        ```

3. Run the application:
        ```sh
        python main.py
        ```

## Usage

1. Launch the application.
2. Select the directory containing the media files you want to compress.
3. Click on "Start Application" to begin the compression process.
4. Monitor the progress through the UI, which shows the elapsed time, ETA, and current file being processed.
5. Use the "Stop Operation" button to halt the process if needed.

## Testing

To run the tests, use the following command:
```sh
pytest
```

## Logging

Logs are saved in the `app.log` file located in the output directory specified during setup.

## Build and Release

The project uses GitHub Actions for CI/CD. The workflow includes testing on Windows and Ubuntu, building the executable with `pyinstaller`, and creating an installer using Inno Setup.

## Contributing

Contributions are welcome! Please fork the repository and submit pull requests.

## Contact

For any issues or feature requests, please open an issue on the GitHub repository.
