import logging
import pytest
from unittest import mock
from utils.video.config import VIDEO_CODECS
import os
import ffmpeg
from utils.video.video_compressor import VideoCompressor
from unittest.mock import MagicMock, patch
import os
from pathlib import Path

# Test setup
@pytest.fixture
def mock_logger():
    with mock.patch("utils.video.video_compressor.VideoCompressor.LOGGER") as mock_logger:
        yield mock_logger


@pytest.fixture
def mock_ffmpeg():
    with mock.patch('ffmpeg.probe') as mock_probe, \
         mock.patch('ffmpeg.input') as mock_input:
        yield mock_probe, mock_input


@pytest.fixture
def mock_os_walk():
    with mock.patch('os.walk') as mock_walk:
        yield mock_walk

def test_is_video_processed(mock_ffmpeg, mock_logger):
    # Arrange
    mock_probe, _ = mock_ffmpeg
    file_path = "path/to/video.mp4"
    mock_probe.return_value = {'format': {'tags': {'comment': 'compressed'}}}

    # Act
    result = VideoCompressor.is_video_proccessed(file_path)

    # Assert
    assert result is True
    mock_logger.error.assert_not_called()

def test_is_video_processed_error(mock_ffmpeg, mock_logger):
    # Arrange
    mock_probe, _ = mock_ffmpeg
    file_path = "path/to/video.mp4"
    mock_error = ffmpeg.Error("Error parsing metadata", b"", b"Error parsing metadata")
    mock_probe.side_effect = mock_error

    # Act
    result = VideoCompressor.is_video_proccessed(file_path)

    # Assert
    assert result is False
    mock_logger.error.assert_called_once_with(
        f"Error while parsing metadata for video:{file_path}. ERROR MESSGAGE: {mock_error.stderr.decode()}"
    )

def test_get_bitrate(mock_ffmpeg, mock_logger):
    # Arrange
    mock_probe, _ = mock_ffmpeg
    input_file = "path/to/video.mp4"
    mock_probe.return_value = {'format': {'bit_rate': '5000000'}}

    # Act
    bitrate = VideoCompressor.get_bitrate(input_file)

    # Assert
    assert bitrate == "1000K"
    mock_logger.error.assert_not_called()

def test_get_bitrate_error(mock_ffmpeg, mock_logger):
    # Arrange
    mock_probe, _ = mock_ffmpeg
    input_file = "path/to/video.mp4"
    mock_error = ffmpeg.Error(
        "Error calculating bitrate",
        b"",
        b"Error calculating bitrate"
    )
    mock_probe.side_effect = mock_error

    # Act
    with pytest.raises(ffmpeg.Error):
        VideoCompressor.get_bitrate(input_file)

    # Assert
    mock_logger.error.assert_called_once_with(
        "Error while calculating bitrate for video:path/to/video.mp4. ERROR MESSGAGE: Error calculating bitrate"
    )


def test_is_codec_available(mock_ffmpeg, mock_logger):
    # Arrange
    codec = "h264_qsv"
    mock_ffmpeg[1].compile.return_value = ["dummy command"]

    # Act
    result = VideoCompressor.is_codec_available(codec)

    # Assert
    assert result is True
    mock_logger.error.assert_not_called()

def test_is_codec_available_error(mock_ffmpeg, mock_logger):
    # Arrange
    codec = "h264_qsv"
    _, mock_input = mock_ffmpeg
    mock_error = ffmpeg.Error(
        "Codec unavailable",
        b"mock stdout",
        b"Codec unavailable"
    )
    mock_input.return_value.output.return_value.global_args.return_value.compile.side_effect = mock_error

    # Act
    result = VideoCompressor.is_codec_available(codec)

    # Assert
    assert result is False
    mock_logger.error.assert_called_once_with(
        "Error while detecting CODEC:h264_qsv. ERROR MESSGAGE: Codec unavailable"
    )

def test_select_best_codec(mock_ffmpeg, mock_logger):
    # Arrange
    VideoCompressor.is_codec_available = mock.MagicMock(return_value=True)

    # Act
    result = VideoCompressor.select_best_codec()

    # Assert
    assert result == VIDEO_CODECS[0]

def test_select_best_codec_no_available(mock_ffmpeg, mock_logger):
    # Arrange
    VideoCompressor.is_codec_available = mock.MagicMock(return_value=False)

    # Act
    with pytest.raises(RuntimeError, match="No supported video codec is available."):
        VideoCompressor.select_best_codec()
        
    # Assert
    mock_logger.error.assert_not_called()

def test_compress_video_qsv(mock_ffmpeg, mock_logger):
    # Arrange
    input_file = "path/to/input.mp4"
    output_file = "path/to/output.mp4"
    bitrate = "1000K"
    framerate = 30
    _, mock_input = mock_ffmpeg
    mock_run = MagicMock(return_value=None)
    mock_input.return_value.output.return_value.global_args.return_value.run = mock_run

    # Act
    VideoCompressor.compress_video_qsv(input_file, output_file, bitrate, framerate)
    
    # Assert
    mock_run.assert_called_once()
    mock_logger.info.assert_called_once_with(f"Compressed video:{input_file} to {output_file}")


def test_compress_video_qsv_error(mock_ffmpeg, mock_logger):
    # Arrange
    input_file = "path/to/input.mp4"
    output_file = "path/to/output.mp4"
    bitrate = "1000K"
    framerate = 30
    _, mock_input = mock_ffmpeg
    mock_error = ffmpeg.Error(
        "Compression failed",
        b"mock stdout",
        b"Compression failed"
    )
    mock_input.return_value.output.return_value.global_args.return_value.run.side_effect = mock_error

    # Act
    VideoCompressor.compress_video_qsv(input_file, output_file, bitrate, framerate)

    # Assert
    mock_logger.error.assert_called_once_with(
        f"An error occurred while encoding:{input_file}. ERROR MESSGAGE: Compression failed"
    )


def test_get_video_files(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/videos"
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4", "video2.avi"])]
    VideoCompressor.is_video_proccessed = mock.MagicMock(return_value=False)

    # Act
    result = VideoCompressor.get_video_files(input_directory)

    # Assert
    assert "video1.mp4" in [os.path.basename(file) for file in result]
    assert "video2.avi" in [os.path.basename(file) for file in result]

def test_get_video_files_processed(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/videos"
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4", "video2.avi"])]
    VideoCompressor.is_video_proccessed = mock.MagicMock(return_value=True)

    # Act
    result = VideoCompressor.get_video_files(input_directory)

    # Assert
    assert len(result) == 0

def test_compress_videos_in_directory(mock_os_walk, mock_ffmpeg, mock_logger):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4", "video2.mp4"])]
    VideoCompressor.is_video_proccessed = mock.MagicMock(return_value=False)
    VideoCompressor.get_bitrate = mock.MagicMock(return_value="1000K")
    VideoCompressor.is_codec_available = mock.MagicMock(return_value=True)
    VideoCompressor.compress_video = mock.MagicMock()

    # Act
    VideoCompressor.compress_videos_in_directory(input_directory, output_directory)

    # Assert
    VideoCompressor.compress_video.assert_called()


def test_compress_videos_in_directory_error(mock_os_walk, mock_ffmpeg):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4"])]
    VideoCompressor.is_video_proccessed = mock.MagicMock(return_value=False)
    VideoCompressor.get_bitrate = mock.MagicMock(return_value="1000K")
    VideoCompressor.compress_video.side_effect = Exception("Compression error")

    # Normalize paths to always use forward slashes
    normalized_input_directory = str(Path(input_directory)).replace('\\', '/')

    expected_message = f"Uncaught error occurred while compressing:{normalized_input_directory}/video1.mp4. ERROR MESSGAGE: Compression error"

    # Mock the logger explicitly
    with patch.object(logging, 'getLogger', return_value=mock.MagicMock()) as mock_get_logger:
        mock_logger = mock_get_logger.return_value

        # Act
        try:
            VideoCompressor.compress_videos_in_directory(input_directory, output_directory)
        except Exception:
            pass  # Catch exception to ensure the test runs even if an error occurs

        # Assert that the error method was called
        assert mock_logger.error.called, "Logger's error method was not called"

        # Normalize both expected and actual messages to use forward slashes for comparison
        actual_message = mock_logger.error.call_args[0][0].replace('\\', '/')
        assert actual_message == expected_message, f"Expected: {expected_message}, but got: {actual_message}"