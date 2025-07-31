# demucs-api/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && \
    apt-get install -y ffmpeg git && \
    pip install demucs && \
    pip install soundfile

# Copy your code
COPY . .

CMD ["python", "demucs_runner.py"]
