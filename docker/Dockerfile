
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies commonly required by pygame and multimedia libs
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		build-essential \
		libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
		libportmidi-dev ffmpeg pkg-config \
	&& rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip \
	&& pip install --no-cache-dir -r ./requirements.txt

# Copy project files (expecting the build context to be the repository root)
COPY . .

# Default command runs the game's main module. Adjust if your entrypoint differs.
CMD ["python", "main.py"]

