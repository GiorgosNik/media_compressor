import piexif
import pytest
from unittest import mock
from utils.images.image_compressor import ImageCompressor
from unittest.mock import MagicMock, patch
import os
from PIL import Image

# Test setup
@pytest.fixture
def mock_logger():
    with mock.patch("utils.images.image_compressor.ImageCompressor.LOGGER") as mock_logger:
        yield mock_logger

@pytest.fixture
def mock_os_walk():
    with mock.patch('os.walk') as mock_walk:
        yield mock_walk

@pytest.fixture
def mock_image_open():
    with mock.patch('PIL.Image.open') as mock_open:
        yield mock_open

@patch("utils.images.image_compressor.piexif.load")  # Adjust path based on actual import
@patch("utils.images.image_compressor.Image.open")
@patch("utils.images.image_compressor.ImageCompressor.LOGGER")
def test_is_processed(mock_logger, mock_image_open, mock_piexif_load):
    # Arrange
    file_path = "path/to/image.jpg"
    mock_img = mock_image_open.return_value.__enter__.return_value
    mock_img.info = {"exif": b"mock_exif"}
    mock_img.format = "JPEG"

    mock_piexif_load.return_value = {
        "0th": {piexif.ImageIFD.ImageDescription: b"Processed"}
    }

    # Act
    result = ImageCompressor.is_processed(file_path)

    # Assert
    assert result is True
    mock_logger.error.assert_not_called()

def test_is_processed_error(mock_image_open, mock_logger):
    # Arrange
    file_path = "path/to/image.jpg"
    mock_image_open.side_effect = Exception("Error reading image")

    # Act
    result = ImageCompressor.is_processed(file_path)

    # Assert
    assert result is False
    mock_logger.error.assert_called_once_with(
        f"An error occurred while reading metadata from image: {file_path}. ERROR MESSAGE: Error reading image"
    )

def test_get_image_files(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/images"
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg", "image2.png"])]
    ImageCompressor.is_processed = mock.MagicMock(return_value=False)

    # Act
    result = ImageCompressor.get_image_files(input_directory)

    # Assert
    assert "image1.jpg" in [os.path.basename(file) for file in result]
    assert "image2.png" in [os.path.basename(file) for file in result]

def test_get_image_files_processed(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/images"
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg", "image2.png"])]
    ImageCompressor.is_processed = mock.MagicMock(return_value=True)

    # Act
    result = ImageCompressor.get_image_files(input_directory)

    # Assert
    assert len(result) == 0

@patch("utils.images.image_compressor.Image.open")
@patch("utils.images.image_compressor.ImageCompressor.LOGGER")
def test_compress_image(mock_logger, mock_image_open):
    # Arrange
    input_file = "path/to/input.jpg"
    output_file = "path/to/output.jpg"
    
    # Mock the image object returned by Image.open
    mock_img = MagicMock()
    mock_img.width = 800  # Set a concrete width
    mock_img.height = 600  # Set a concrete height
    mock_resized_img = MagicMock()  # Mock the resized image
    mock_img.resize.return_value = mock_resized_img
    mock_image_open.return_value.__enter__.return_value = mock_img

    # Act
    ImageCompressor.compress_image(input_file, output_file)

    # Assert
    mock_img.resize.assert_called_once_with((400, 300), Image.LANCZOS)
    mock_resized_img.save.assert_called_once_with(output_file, optimize=True, quality=85)
    mock_logger.info.assert_called_once_with(f"Image {input_file} saved successfully to: {output_file}")

def test_compress_image_error(mock_image_open, mock_logger):
    # Arrange
    input_file = "path/to/input.jpg"
    output_file = "path/to/output.jpg"
    mock_image_open.side_effect = Exception("Compression error")

    # Act
    ImageCompressor.compress_image(input_file, output_file)

    # Assert
    mock_logger.error.assert_called_once_with(
        f"An error occurred while compressing image: {input_file}. ERROR MESSAGE: Compression error"
    )

def test_compress_images_in_directory(mock_os_walk, mock_image_open, mock_logger):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg", "image2.png"])]
    ImageCompressor.is_processed = mock.MagicMock(return_value=False)
    ImageCompressor.get_image_files = mock.MagicMock(return_value=["path/to/input/image1.jpg", "path/to/input/image2.png"])
    ImageCompressor.compress_image = mock.MagicMock()
    ImageCompressor.add_metadata = mock.MagicMock()

    # Act
    ImageCompressor.compress_images_in_directory(input_directory, output_directory)

    # Assert
    ImageCompressor.compress_image.assert_called()
    ImageCompressor.add_metadata.assert_called()
    mock_logger.info.assert_called_with(f"Finished compressing images in directory: {input_directory}")

def test_compress_images_in_directory_error(mock_os_walk, mock_image_open, mock_logger):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg"])]
    ImageCompressor.is_processed = mock.MagicMock(return_value=False)
    ImageCompressor.get_image_files = mock.MagicMock(return_value=["path/to/input/image1.jpg"])
    ImageCompressor.compress_image.side_effect = Exception("Compression error")

    # Act
    ImageCompressor.compress_images_in_directory(input_directory, output_directory)

    # Assert
    mock_logger.error.assert_called_once_with(
        "Uncaught error occurred while compressing image: path/to/input/image1.jpg. ERROR MESSAGE: Compression error"
    )