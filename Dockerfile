# Use Python 3.12 to match your compiled .pyc versions
FROM python:3.12-slim

# Install system dependencies for GUI (Tkinter) and Audio (Pygame/ALSA)
RUN apt-get update && apt-get install -y \
    python3-tk \
    libasound2 \
    libsdl2-mixer-2.0-0 \
    libx11-6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
RUN pip install --no-cache-dir \
    customtkinter \
    pygame \
    requests \
    mpremote

# Copy the project files
COPY . .

# Ensure the utils directory exists for the audio list
RUN mkdir -p utils

# Default command to run the chatbot
CMD ["python", "chatbot.py"]