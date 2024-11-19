FROM python:3.11-slim

# Install system-level dependencies, including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Upgrade pip to the latest version
RUN pip install --upgrade pip --root-user-action=ignore

# Set the working directory in the container
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install Python dependencies
RUN pip install -r requirements.txt

# Create the staticfiles directory
RUN mkdir -p staticfiles

# Run migrations (ignore errors if database is unavailable during build)
RUN python manage.py makemigrations --noinput || true
RUN python manage.py migrate --noinput || true

# Collect static files
ARG ENV=development
RUN if [ "$ENV" = "production" ]; then python manage.py collectstatic --noinput; fi

# Expose the port your application will run on
EXPOSE 8000

# Command to run your application
CMD ["gunicorn", "FFLO_backend.wsgi:application", "--bind", "0.0.0.0:8000"]
