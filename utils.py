import subprocess

def convert_to_webp(input_image_path, output_image_path):
    # Run the FFmpeg command to convert to .webp with YUV color format
    try:
        subprocess.run(
            ['ffmpeg', '-i', input_image_path, '-pix_fmt', 'yuv420p', '-q:v', '80', output_image_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error converting image to .webp: {e}")
        raise e