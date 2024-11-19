FROM python:3.11-slim

# Install system-level dependencies, including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose the port your application will run on
EXPOSE 8000

# Command to run your application
CMD ["gunicorn", "FFLO_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
