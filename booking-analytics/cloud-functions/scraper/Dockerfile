# Use the official Python runtime as a parent image
# Python 3.11 slim provides a good balance of features and size
FROM python:3.11-slim

# Set environment variables for Python optimization
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory inside the container
# This is where our application code will live
WORKDIR /app

# Install system dependencies required for some Python packages
# build-essential is needed for compiling certain Python packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/* 

# Copy and install Python dependencies first
# This is done before copying code to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
# The . copies everything from current directory to /app in container
COPY . .

# Create a non-root user for security
# Running as non-root is a security best practice
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser /app
USER appuser

# Expose the port that the app runs on
# Cloud Run expects applications to listen on the PORT environment variable
EXPOSE 8080

# Run the application
# This starts our Flask application when the container starts
CMD ["python", "main.py"]