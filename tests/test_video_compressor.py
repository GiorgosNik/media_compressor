import json
import logging
import subprocess
import pytest
from unittest import mock
from utils.video.config import VIDEO_CODECS
import os
import ffmpeg
from utils.video.video_compressor import VideoCompressor
from unittest.mock import patch
import os
from utils.handler.handler import Handler

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
        
@pytest.fixture
def mock_os_path_isdir():
    with mock.patch('os.path.isdir') as mock_path_isdir:
        yield mock_path_isdir
             
def test_is_video_processed(mock_logger):
    # Arrange
    file_path = "path/to/video.mp4"
    mock_result = mock.Mock()
    mock_result.stdout = json.dumps({
        "format": {
            "tags": {
                "comment": "compressed"
            }
        }
    })
    mock_result.returncode = 0

    with mock.patch('subprocess.run', return_value=mock_result):
        # Act
        result = VideoCompressor.is_video_processed(file_path)

        # Assert
        assert result is True
        mock_logger.error.assert_not_called()

def test_is_video_processed_uncompressed(mock_logger):
    # Arrange  
    file_path = "path/to/video.mp4"
    mock_result = mock.Mock()
    mock_result.stdout = json.dumps({
        "format": {
            "tags": {
                "comment": "not_compressed"
            }
        }
    })
    mock_result.returncode = 0

    with mock.patch('subprocess.run', return_value=mock_result):
        # Act
        result = VideoCompressor.is_video_processed(file_path)

        # Assert
        assert result is False
        mock_logger.error.assert_not_called()

def test_is_video_processed_error(mock_logger):
    # Arrange
    file_path = "path/to/video.mp4"
    mock_error = Exception("ffprobe error")
    
    with mock.patch('subprocess.run', side_effect=mock_error):
        # Act
        result = VideoCompressor.is_video_processed(file_path)

        # Assert 
        assert result is False
        mock_logger.error.assert_called_once_with(
            f"Error while parsing metadata for video:{file_path}. ERROR MESSAGE: ffprobe error"
        )

def test_get_bitrate(mock_logger):
    # Arrange
    input_file = "path/to/video.mp4"
    mock_result = mock.Mock()
    mock_result.stdout = json.dumps({
        "format": {
            "bit_rate": "5000000"  # 5Mbps
        }
    })
    mock_result.returncode = 0

    with mock.patch('subprocess.run', return_value=mock_result):
        # Act
        result = VideoCompressor.get_bitrate(input_file)

        # Assert
        assert result == "1000K"  # Expected bitrate after compression (5Mbps/5)
        mock_logger.error.assert_not_called()

def test_get_bitrate_error(mock_logger):
    # Arrange
    input_file = "path/to/video.mp4"
    mock_error = Exception("ffprobe error")
    
    with mock.patch('subprocess.run', side_effect=mock_error):
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            VideoCompressor.get_bitrate(input_file)
        
        assert str(exc_info.value) == "ffprobe error"
        mock_logger.error.assert_called_once_with(
            f"Error while calculating bitrate for video:{input_file}. ERROR MESSAGE: ffprobe error"
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
        "Error while detecting CODEC:h264_qsv. ERROR MESSAGE: Codec unavailable"
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

@patch('subprocess.run')
def test_compress_video_qsv(mock_subprocess_run, mock_logger):
    # Arrange
    input_file = "path/to/input.mp4" 
    output_file = "path/to/output.mp4"
    bitrate = "1000K"
    framerate = 30
    mock_subprocess_run.return_value = mock.Mock(returncode=0)

    # Act
    VideoCompressor.compress_video_qsv(input_file, output_file, bitrate, framerate)

    # Assert
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[0][0] == [
        'ffmpeg',
        '-i', input_file,
        '-b:v', bitrate,
        '-vcodec', 'h264_qsv', 
        '-r', str(framerate),
        '-metadata', 'comment=compressed',
        '-preset', 'medium',
        '-loglevel', 'error',
        output_file
    ]
    mock_logger.info.assert_called_once_with(
        f"Compressed video: {input_file} to {output_file}"
    )

def test_compress_video_qsv_subprocess_error(mock_logger):
    # Arrange
    input_file = "path/to/input.mp4"
    output_file = "path/to/output.mp4" 
    bitrate = "1000K"
    framerate = 30
    error_message = "Subprocess error"
    mock_error = subprocess.CalledProcessError(
        1, "cmd", stderr=error_message.encode()
    )

    with mock.patch("subprocess.run", side_effect=mock_error):
        # Act
        VideoCompressor.compress_video_qsv(input_file, output_file, bitrate, framerate)

        # Assert
        mock_logger.error.assert_called_once_with(
            f"An error occurred while encoding: {input_file}. ERROR MESSAGE: {error_message}"
        )
        
def test_get_video_files(mock_os_walk, mock_os_path_isdir, mock_logger):
    # Arrange
    input_directory = "path/to/videos"
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4", "video2.avi"])]
    mock_os_path_isdir.return_value = True
    VideoCompressor.is_video_processed = mock.MagicMock(return_value=False)

    # Act
    result = VideoCompressor.get_video_files(input_directory)

    # Assert
    assert "video1.mp4" in [os.path.basename(file) for file in result]
    assert "video2.avi" in [os.path.basename(file) for file in result]

def test_get_video_files_processed(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/videos"
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4", "video2.avi"])]
    VideoCompressor.is_video_processed = mock.MagicMock(return_value=True)

    # Act
    result = VideoCompressor.get_video_files(input_directory)

    # Assert
    assert len(result) == 0

def test_compress_videos_in_directory(mock_os_walk, mock_os_path_isdir, mock_logger):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    progress_callback = mock.Mock()
    mock_os_walk.return_value = [(input_directory, [], ["video1.mp4", "video2.avi"])]
    mock_os_path_isdir.return_value = True
    
    with mock.patch.multiple(VideoCompressor,
        select_best_codec=mock.Mock(return_value="h264_qsv"),
        get_video_files=mock.Mock(return_value=["path/to/input/video1.mp4", "path/to/input/video2.avi"]),
        get_bitrate=mock.Mock(return_value="1000K"),
        compress_video=mock.Mock(),
        is_video_processed=mock.Mock(return_value=False)), \
        mock.patch('os.path.getsize', return_value=1000000), \
        mock.patch('os.makedirs'):

        # Act
        VideoCompressor.compress_videos_in_directory(
            input_directory,
            output_directory, 
            progress_callback=progress_callback
        )

        # Assert
        VideoCompressor.select_best_codec.assert_called_once()
        VideoCompressor.get_video_files.assert_called_once_with(input_directory)
        assert VideoCompressor.compress_video.call_count == 2
        progress_callback.assert_called()

@patch('subprocess.run')
def test_compress_video_cpu(mock_subprocess_run, mock_logger):
    # Arrange
    input_file = "path/to/input.mp4"
    output_file = "path/to/output.mp4"
    bitrate = "1000K" 
    framerate = 30
    mock_subprocess_run.return_value = mock.Mock(returncode=0)

    # Act
    VideoCompressor.compress_video_cpu(input_file, output_file, bitrate, framerate)

    # Assert
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[0][0] == [
        'ffmpeg',
        '-i', input_file,
        '-b:v', bitrate,
        '-vcodec', 'libx264',
        '-r', str(framerate), 
        '-metadata', 'comment=compressed',
        '-loglevel', 'error',
        output_file
    ]
    mock_logger.info.assert_called_once_with(
        f"Compressed video: {input_file} to {output_file}"
    )

def test_compress_video_cpu_error(mock_logger):
    # Arrange
    input_file = "path/to/input.mp4"
    output_file = "path/to/output.mp4"
    bitrate = "1000K"
    framerate = 30
    error_message = "Subprocess error"
    mock_error = subprocess.CalledProcessError(
        1, "cmd", stderr=error_message.encode()
    )

    with mock.patch("subprocess.run", side_effect=mock_error):
        # Act
        VideoCompressor.compress_video_cpu(input_file, output_file, bitrate, framerate)

        # Assert
        mock_logger.error.assert_called_once_with(
            f"An error occurred while encoding: {input_file}. ERROR MESSAGE: {error_message}"
        )

@patch('subprocess.run')
def test_convert_incompatible_video(mock_subprocess_run, mock_logger):
    # Arrange
    input_file = "path/to/input.mkv"
    output_file = "path/to/output.mp4"
    mock_subprocess_run.return_value = mock.Mock(returncode=0)

    # Act
    VideoCompressor.convert_incompatible_video(input_file, output_file)

    # Assert
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[0][0] == [
        'ffmpeg',
        '-i', input_file,
        '-c:v', 'libx264',
        '-crf', '23',
        '-metadata', 'comment=compressed',
        '-preset', 'medium', 
        output_file
    ]
    mock_logger.info.assert_called_once_with(
        f"Converted video: {input_file} to {output_file}"
    )

def test_convert_incompatible_video_error(mock_logger):
    # Arrange 
    input_file = "path/to/input.mkv"
    output_file = "path/to/output.mp4"
    error_message = "Subprocess error"
    mock_error = subprocess.CalledProcessError(
        1, "cmd", stderr=error_message.encode()
    )

    with mock.patch("subprocess.run", side_effect=mock_error):
        # Act
        VideoCompressor.convert_incompatible_video(input_file, output_file)

        # Assert
        mock_logger.error.assert_called_once_with(
            f"An error occurred while converting: {input_file}. ERROR MESSAGE: {error_message}"
        )
def test_convert_incompatible_videos_in_directory_and_compress(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    mock_os_walk.return_value = [(input_directory, [], ["video1.h264", "video2.h264"])]
    
    VideoCompressor.is_video_processed = mock.MagicMock(return_value=False)
    VideoCompressor.convert_incompatible_video = mock.MagicMock()
    
    with mock.patch('os.path.getsize', return_value=1000000):
        # Act
        VideoCompressor.convert_incompatible_videos_in_directory_and_compress(
            input_directory, 
            output_directory,
            progress_callback=None
        )

    # Assert
    VideoCompressor.convert_incompatible_video.assert_called()

@patch('subprocess.run')
def test_convert_incompatible_video(mock_subprocess_run, mock_logger):
    # Arrange
    input_file = "path/to/input.mkv"
    output_file = "path/to/output.mp4"
    mock_subprocess_run.return_value = mock.Mock(returncode=0)

    # Act
    VideoCompressor.convert_incompatible_video(input_file, output_file)

    # Assert
    mock_subprocess_run.assert_called_once()
    assert mock_subprocess_run.call_args[0][0] == [
        'ffmpeg',
        '-i', input_file,
        '-c:v', 'libx264',
        '-crf', '23',
        '-metadata', 'comment=compressed',
        '-preset', 'medium', 
        output_file
    ]
    mock_logger.info.assert_called_once_with(
        f"Converted video: {input_file} to {output_file}"
    )

def test_convert_incompatible_video_error(mock_logger):
    # Arrange 
    input_file = "path/to/input.mkv"
    output_file = "path/to/output.mp4"
    error_message = "Subprocess error"
    mock_error = subprocess.CalledProcessError(
        1, "cmd", stderr=error_message.encode()
    )

    with mock.patch("subprocess.run", side_effect=mock_error):
        # Act
        VideoCompressor.convert_incompatible_video(input_file, output_file)

        # Assert
        mock_logger.error.assert_called_once_with(
            f"An error occurred while converting: {input_file}. ERROR MESSAGE: {error_message}"
        ) 
        
@mock.patch('utils.handler.handler.VideoCompressor')
@mock.patch('utils.handler.handler.ImageCompressor')
@mock.patch('utils.handler.handler.setup_logging')
def test_start_compression(mock_setup_logging, mock_image_compressor, mock_video_compressor, mock_logger):
    # Arrange
    input_directory = "path/to/input"
    process_video = True
    process_image = True 
    convert_incompatible = True
    progress_callback = mock.Mock()

    # Act
    Handler.start_compression(
        input_directory=input_directory,
        process_video=process_video,
        process_image=process_image, 
        convert_incompatible=convert_incompatible,
        progress_callback=progress_callback
    )

    # Assert
    mock_setup_logging.assert_called_once()
    mock_video_compressor.compress_videos_in_directory.assert_called_once_with(
        input_directory, 
        mock.ANY, 
        progress_callback
    )
    mock_image_compressor.compress_images_in_directory.assert_called_once_with(
        input_directory,
        mock.ANY,  
        progress_callback
    )
    mock_video_compressor.convert_incompatible_videos_in_directory_and_compress.assert_called_once_with(
        input_directory,
        mock.ANY,  
        progress_callback
    )

