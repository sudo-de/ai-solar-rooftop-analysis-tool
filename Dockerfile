# Use official Python 3.13 slim image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y git git-lfs
RUN apt-get update && apt-get install -y \
    build-essential \
    git-lfs \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
RUN git lfs install

# Copy requirements first to leverage caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py streamlit_app.py test_main.py generate_sample_image.py generate_screenshots.py ./

# Conditionally copy samples and screenshots if exists
COPY samples/ samples/
COPY screenshots/ screenshots/

# Copy documentation
COPY Implementation_Documentation.md Example_Analyses.md Performance_Metrics.md README.md ./

# Copy .env if it exists
COPY .env* ./

# Create runtime directories
RUN mkdir -p logs outputs temp

# Generate samples and screenshots
RUN python generate_sample_image.py
RUN python generate_screenshots.py

# Expose default Streamlit port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.fileWatcherType=none"]
