import os
from PIL import Image
import subprocess

def convert_to_webp(input_image_path, output_image_path):
    try:
        subprocess.run(
            ['ffmpeg', '-i', input_image_path, '-pix_fmt', 'yuv420p', '-q:v', '80', output_image_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error converting image to .webp: {e}")
        raise e

def create_small_image(input_image_path, small_image_webp_path, max_size=20):
    try:
        with Image.open(input_image_path) as img:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            temp_small_image_path = f"{small_image_webp_path}.tmp"
            img.save(temp_small_image_path, 'PNG')

        convert_to_webp(temp_small_image_path, small_image_webp_path)

    except Exception as e:
        print(f"Error resizing and converting small image to .webp: {e}")
        raise e
    finally:
        if os.path.exists(temp_small_image_path):
            os.remove(temp_small_image_path)

def create_user_icon(input_image_path, small_image_webp_path, max_size=60):
    try:
        with Image.open(input_image_path) as img:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            temp_small_image_path = f"{small_image_webp_path}.tmp"
            img.save(temp_small_image_path, 'PNG')

        convert_to_webp(temp_small_image_path, small_image_webp_path)

    except Exception as e:
        print(f"Error resizing and converting small image to .webp: {e}")
        raise e
    finally:
        if os.path.exists(temp_small_image_path):
            os.remove(temp_small_image_path)
