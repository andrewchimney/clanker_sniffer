# whisper-api/Dockerfile
FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install PostgreSQL client libs + pip package
RUN apt-get update && apt-get install -y gcc libpq-dev

COPY . .

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "whisper_runner:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
