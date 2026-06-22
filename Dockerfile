# Use official lightweight Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package descriptors and source code
COPY pyproject.toml .
COPY zimbra/ ./zimbra/
RUN pip install --no-cache-dir -e .

# Copy additional app files
COPY app.py app_runner.py .

# Expose port
EXPOSE 8080

# Command to run on container startup
CMD ["python", "app_runner.py"]
