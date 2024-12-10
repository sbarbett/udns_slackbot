# Base Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy files into the container
COPY requirements.txt ./
COPY ./app/ .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure /data directory exists for persistent config
RUN mkdir -p /data

# Set environment variables for Python and logging
ENV PYTHONUNBUFFERED=1

# Run both initialize.py and app.py concurrently
CMD ["bash", "-c", "python initialize.py && exec python app.py"]
