FROM selenium/standalone-chrome:latest

# Switch to root to install Python and dependencies
USER root

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Expose port for Flask
EXPOSE 8080

# Start Xvfb and run the application
CMD ["python3", "sms_hadi.py"]
