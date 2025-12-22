import piexif
import pytest
from unittest import mock
from utils.images.image_compressor import ImageCompressor
from unittest.mock import MagicMock, patch, ANY
import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# --- Fixtures ---
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

@pytest.fixture
def mock_getsize():
    with mock.patch('os.path.getsize') as mock_size:
        yield mock_size

# --- Tests ---

@patch("utils.images.image_compressor.piexif.load")
def test_is_processed_jpeg(mock_piexif_load, mock_image_open, mock_logger):
    # Arrange
    file_path = "path/to/image.jpg"
    mock_img = mock_image_open.return_value.__enter__.return_value
    mock_img.info = {"exif": b"mock_exif"}
    
    # Mock return value containing the specific compressed message
    mock_piexif_load.return_value = {
        "0th": {piexif.ImageIFD.ImageDescription: ImageCompressor.COMPRESSED_MESSAGE.encode('utf-8')}
    }

    # Act
    result = ImageCompressor.is_processed(file_path)

    # Assert
    assert result is True
    mock_logger.error.assert_not_called()

def test_is_processed_png(mock_image_open, mock_logger):
    # Arrange
    file_path = "path/to/image.png"
    mock_img = mock_image_open.return_value.__enter__.return_value
    # Mock PNG comment
    mock_img.info = {"Comment": ImageCompressor.COMPRESSED_MESSAGE}

    # Act
    result = ImageCompressor.is_processed(file_path)

    # Assert
    assert result is True

def test_is_processed_error(mock_image_open, mock_logger):
    # Arrange
    file_path = "path/to/image.jpg"
    mock_image_open.side_effect = Exception("Error reading image")

    # Act
    result = ImageCompressor.is_processed(file_path)

    # Assert
    assert result is False
    # Note: Logic was updated to check logger existence, fixture provides it
    mock_logger.error.assert_called_with(
        f"Error checking metadata for: {file_path}. ERROR: Error reading image"
    )

def test_get_image_files(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/images"
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg", "image2.png"])]
    
    # Mock is_processed to return False (files are not yet processed)
    with patch.object(ImageCompressor, 'is_processed', return_value=False):
        # Act
        result = ImageCompressor.get_image_files(input_directory)

    # Assert
    assert len(result) == 2
    assert "image1.jpg" in [os.path.basename(file) for file in result]

def test_get_image_files_skips_processed(mock_os_walk, mock_logger):
    # Arrange
    input_directory = "path/to/images"
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg", "image2.png"])]
    
    # Mock is_processed to return True (files SHOULD be skipped)
    with patch.object(ImageCompressor, 'is_processed', return_value=True):
        # Act
        result = ImageCompressor.get_image_files(input_directory)

    # Assert
    assert len(result) == 0

@patch("utils.images.image_compressor.piexif.dump")
@patch("utils.images.image_compressor.piexif.load")
def test_compress_and_tag_image_jpeg(mock_piexif_load, mock_piexif_dump, mock_image_open, mock_logger):
    # Arrange
    input_file = "path/to/input.jpg"
    output_file = "path/to/output.jpg"
    
    mock_img = MagicMock()
    mock_img.width = 800 
    mock_img.height = 600
    mock_img.info = {"exif": b"original_exif"}
    
    mock_resized_img = MagicMock()
    mock_img.resize.return_value = mock_resized_img
    mock_image_open.return_value.__enter__.return_value = mock_img

    # Mock EXIF handling
    mock_piexif_load.return_value = {"0th": {}}
    mock_piexif_dump.return_value = b"new_modified_exif"

    # Act
    ImageCompressor.compress_and_tag_image(input_file, output_file)

    # Assert
    # Check resize
    mock_img.resize.assert_called_once_with((400, 300), Image.LANCZOS)
    
    # Check save was called with 'exif' kwarg
    mock_resized_img.save.assert_called_once_with(
        output_file, 
        "jpeg", 
        optimize=True, 
        quality=85, 
        exif=b"new_modified_exif"
    )
    mock_logger.info.assert_called_with(f"Image {input_file} compressed and saved to: {output_file}")

def test_compress_and_tag_image_png(mock_image_open, mock_logger):
    # Arrange
    input_file = "path/to/input.png"
    output_file = "path/to/output.png"
    
    mock_img = MagicMock()
    mock_img.width = 800 
    mock_img.height = 600
    
    mock_resized_img = MagicMock()
    mock_img.resize.return_value = mock_resized_img
    mock_image_open.return_value.__enter__.return_value = mock_img

    # Act
    ImageCompressor.compress_and_tag_image(input_file, output_file)

    # Assert
    # Check save was called with 'pnginfo' kwarg
    mock_resized_img.save.assert_called_once()
    args, kwargs = mock_resized_img.save.call_args
    assert args[0] == output_file
    assert kwargs['optimize'] is True
    assert isinstance(kwargs['pnginfo'], PngInfo) 

def test_compress_and_tag_image_error(mock_image_open, mock_logger):
    # Arrange
    input_file = "path/to/input.jpg"
    output_file = "path/to/output.jpg"
    mock_image_open.side_effect = Exception("Compression fail")

    # Act
    ImageCompressor.compress_and_tag_image(input_file, output_file)

    # Assert
    mock_logger.error.assert_called_once_with(
        f"An error occurred while compressing image: {input_file}. ERROR MESSAGE: Compression fail"
    )

@patch("utils.images.image_compressor.logging.getLogger")
def test_compress_images_in_directory_success(mock_get_logger, mock_getsize, mock_os_walk):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    
    mock_logger = mock.Mock()
    mock_get_logger.return_value = mock_logger
    
    # Return two files
    mock_os_walk.return_value = [(input_directory, [], ["image1.jpg", "image2.png"])]
    
    # Mock size to be LARGER than threshold (500kB = 512000 bytes)
    mock_getsize.return_value = 600000 

    # Mock internal methods
    with patch.object(ImageCompressor, "is_processed", return_value=False), \
         patch.object(ImageCompressor, "compress_and_tag_image") as mock_compress_tag:

        # Act
        ImageCompressor.compress_images_in_directory(input_directory, output_directory)

        # Assert
        assert mock_compress_tag.call_count == 2
        mock_compress_tag.assert_any_call(
            os.path.join(input_directory, "image1.jpg"),
            os.path.join(output_directory, "image1.jpg")
        )
        mock_logger.info.assert_any_call(f"Finished compressing images in directory: {input_directory}")

@patch("utils.images.image_compressor.logging.getLogger")
def test_compress_images_in_directory_skips_small_files(mock_get_logger, mock_getsize, mock_os_walk):
    # Arrange
    input_directory = "path/to/input"
    output_directory = "path/to/output"
    mock_logger = mock.Mock()
    mock_get_logger.return_value = mock_logger
    
    mock_os_walk.return_value = [(input_directory, [], ["small.jpg", "large.jpg"])]
    
    # Side effect for getsize: small.jpg is 100kB, large.jpg is 600kB
    def getsize_side_effect(path):
        if "small.jpg" in path:
            return 100 * 1024 # Small
        return 600 * 1024 # Large
    mock_getsize.side_effect = getsize_side_effect

    with patch.object(ImageCompressor, "is_processed", return_value=False), \
         patch.object(ImageCompressor, "compress_and_tag_image") as mock_compress_tag:

        # Act
        ImageCompressor.compress_images_in_directory(input_directory, output_directory)

        # Assert
        # Should only run once for the large file
        assert mock_compress_tag.call_count == 1
        args, _ = mock_compress_tag.call_args
        assert "large.jpg" in args[0]
        
        # Verify the log message for skipping was called
        # We need to check if the specific message was logged
        skip_msg_check = any("Skipping image" in str(call) and "small.jpg" in str(call) for call in mock_logger.info.call_args_list)
        assert skip_msg_check, "Logger should have logged skipping the small file"