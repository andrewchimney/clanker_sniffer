FROM python:3.10-slim

WORKDIR /app



# Copy Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt



# Copy app code
COPY . .

EXPOSE 8000

# Run your fingerprint processor
CMD ["uvicorn", "orchestrator_runner:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
