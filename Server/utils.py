import subprocess

def convert_to_webp(input_image_path, output_image_path):
    try:
        subprocess.run(
            ['ffmpeg', '-i', input_image_path, '-qscale', '80', output_image_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error converting image to .webp: {e}")
        raise e