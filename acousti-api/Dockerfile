FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for audio processing and fingerprinting
RUN apt-get update && \
    apt-get install -y ffmpeg libchromaprint-tools gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*
    




# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



# Copy app code
COPY . .

EXPOSE 8000

# Run your fingerprint processor
CMD ["uvicorn", "acousti_runner:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
