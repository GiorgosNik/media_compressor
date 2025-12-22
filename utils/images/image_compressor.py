import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from utils.logging.logging import setup_logging
from utils.images.config import IMAGE_FILETYPES
import piexif
import logging

class ImageCompressor:
    LOGGER = None
    COMPRESSED_MESSAGE = "compressed"
    SIZE_THRESHOLD_BYTES = 500 * 1024 

    @classmethod
    def compress_images_in_directory(cls, input_directory, output_directory, progress_callback=None):
        setup_logging(output_directory)
        cls.LOGGER = logging.getLogger(__name__)
        cls.LOGGER.debug(f"Started compressing images in directory: {input_directory}")

        image_files = cls.get_image_files(input_directory)

        total_files = len(image_files)
        for idx, input_file in enumerate(image_files, start=1):
            try:
                if progress_callback:
                    progress_callback(idx / total_files, input_file, idx, total_files)

                if os.path.getsize(input_file) <= cls.SIZE_THRESHOLD_BYTES:
                    cls.LOGGER.info(f"Skipping image {input_file}: Size is under 500kB.")
                    continue

                relative_path = os.path.relpath(input_file, input_directory)
                output_file = os.path.join(output_directory, relative_path)
                os.makedirs(os.path.dirname(output_file), exist_ok=True)

                cls.compress_and_tag_image(input_file, output_file)

            except Exception as e:
                cls.LOGGER.error(f"Uncaught error occurred while compressing image: {input_file}. ERROR MESSAGE: {str(e)}")

        if progress_callback:
            progress_callback(1, "", total_files, total_files)
        cls.LOGGER.info(f"Finished compressing images in directory: {input_directory}")

    @classmethod
    def get_image_files(cls, input_directory):
        """Get a list of image files in the specified directory, skipping processed ones."""
        image_files = []
        for root, _, files in os.walk(input_directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in IMAGE_FILETYPES):
                    full_path = os.path.join(root, file)
                    if not cls.is_processed(full_path):
                        image_files.append(full_path)
                    else:
                        if cls.LOGGER:
                            cls.LOGGER.info(f"Skipping already processed file: {full_path}")
        return image_files

    @classmethod
    def is_processed(cls, file_path):
        """Checks if the file has the 'compressed' metadata flag."""
        try:
            with Image.open(file_path) as img:
                if file_path.lower().endswith(('.jpg', '.jpeg', '.tiff')):
                    if "exif" in img.info:
                        try:
                            exif_data = piexif.load(img.info["exif"])
                            description = exif_data["0th"].get(piexif.ImageIFD.ImageDescription, b"")
                            return cls.COMPRESSED_MESSAGE.encode('utf-8') in description
                        except Exception:
                            return False
                    return False

                elif file_path.lower().endswith(".png"):
                    return img.info.get("Comment") == cls.COMPRESSED_MESSAGE
                
        except Exception as e:
            if cls.LOGGER:
                cls.LOGGER.error(f"Error checking metadata for: {file_path}. ERROR: {str(e)}")
        return False

    @classmethod
    def compress_and_tag_image(cls, input_file, output_file):
        """Resizes the image and adds metadata in a single save operation to preserve quality."""
        try:
            with Image.open(input_file) as img:
                new_width = max(1, round(img.width / 2))
                new_height = max(1, round(img.height / 2))
                img = img.resize((new_width, new_height), Image.LANCZOS)

                save_kwargs = {
                    "optimize": True,
                    "quality": 85
                }

                if input_file.lower().endswith(('.jpg', '.jpeg', '.tiff')):
                    if "exif" in img.info:
                        exif_dict = piexif.load(img.info["exif"])
                    else:
                        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
                    
                    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = cls.COMPRESSED_MESSAGE.encode('utf-8')
                    exif_bytes = piexif.dump(exif_dict)
                    save_kwargs["exif"] = exif_bytes
                    format_type = "jpeg"

                elif input_file.lower().endswith(".png"):
                    metadata = PngInfo()
                    metadata.add_text("Comment", cls.COMPRESSED_MESSAGE)
                    save_kwargs["pnginfo"] = metadata
                    format_type = "png"
                else:
                    format_type = img.format

                img.save(output_file, format_type, **save_kwargs)
                
                cls.LOGGER.info(f"Image {input_file} compressed and saved to: {output_file}")

        except Exception as e:
            cls.LOGGER.error(f"An error occurred while compressing image: {input_file}. ERROR MESSAGE: {str(e)}")