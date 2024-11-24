import os
from PIL import Image
from utils.logging.logging import setup_logging
from utils.images.config import IMAGE_FILETYPES
import piexif
import logging

class ImageCompressor:
    setup_logging()  # Set up logging configuration
    LOGGER = logging.getLogger(__name__)

    @classmethod
    def compress_images_in_directory(cls, input_directory, output_directory, progress_callback=None):
        cls.LOGGER.info(f"Started compressing images in directory: {input_directory}")

        # Gather image files
        image_files = cls.get_image_files(input_directory)

        # Process each image file
        total_files = len(image_files)
        for idx, input_file in enumerate(image_files, start=1):
            try:
                # Update progress
                if progress_callback:
                    progress_callback(idx / total_files, input_file, idx, total_files)

                # Calculate output file path
                relative_path = os.path.relpath(input_file, input_directory)
                output_file = os.path.join(output_directory, relative_path)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                # Compress image
                cls.compress_image(input_file, output_file)
                cls.add_metadata(output_file)

            except Exception as e:
                cls.LOGGER.error(f"Uncaught error occurred while compressing image: {input_file}. ERROR MESSAGE: {str(e)}")

        if progress_callback:
            progress_callback(1, "", total_files, total_files)
        cls.LOGGER.info(f"Finished compressing images in directory: {input_directory}")

    @classmethod
    def get_image_files(cls, input_directory):
        """Get a list of image files in the specified directory."""
        image_files = []
        for root, _, files in os.walk(input_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in IMAGE_FILETYPES) and not cls.is_processed(os.path.join(root, file)):
                    image_files.append(os.path.join(root, file))
        return image_files

    @classmethod
    def add_metadata(cls, file_path):
        try:
            with Image.open(file_path) as img:
                if file_path.lower().endswith(('.jpg', '.jpeg', '.tiff')):
                    exif_dict = piexif.load(img.info.get("exif", file_path))
                    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = b"Processed"
                    exif_bytes = piexif.dump(exif_dict)
                    img.save(file_path, "jpeg", exif=exif_bytes)
                elif file_path.lower().endswith(".png"):
                    img.info["Comment"] = "Processed"
                    img.save(file_path, "png")
        except Exception as e:
            cls.LOGGER.error(f"An error occurred while adding metadata to image: {file_path}. ERROR MESSAGE: {str(e)}")

    @classmethod
    def is_processed(cls, file_path):
        try:
            with Image.open(file_path) as img:
                if file_path.lower().endswith(('.jpg', '.jpeg', '.tiff')):
                    exif_data = piexif.load(img.info.get("exif", file_path))
                    return b"Processed" in exif_data["0th"].get(piexif.ImageIFD.ImageDescription, b"")
                elif file_path.lower().endswith(".png"):
                    return img.info.get("Comment") == "Processed"
        except Exception as e:
            cls.LOGGER.error(f"An error occurred while reading metadata from image: {file_path}. ERROR MESSAGE: {str(e)}")
        return False

    @classmethod
    def compress_image(cls, input_file, output_file):
        try:
            with Image.open(input_file) as img:
                # Calculate new size
                new_width = max(1, round(img.width / 2))
                new_height = max(1, round(img.height / 2))
                new_size = (new_width, new_height)
                
                # Resize and save image
                img = img.resize(new_size, Image.LANCZOS)
                img.save(output_file, optimize=True, quality=85)
                cls.LOGGER.info(f"Image {input_file} saved successfully to: {output_file}")
        except Exception as e:
            cls.LOGGER.error(f"An error occurred while compressing image: {input_file}. ERROR MESSAGE: {str(e)}")