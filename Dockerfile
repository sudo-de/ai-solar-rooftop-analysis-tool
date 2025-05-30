# Stage 1: Build dependencies
FROM python:3.13-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev git-lfs \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgl1-mesa-dri mesa-utils gcc && \
    rm -rf /var/lib/apt/lists/* && \
    git lfs install && \
    pip install --no-cache-dir --upgrade pip setuptools wheel
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final image
FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
    libgl1-mesa-dri && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY main.py streamlit_app.py test_main.py generate_sample_image.py generate_screenshots.py ./
COPY samples/ samples/
COPY screenshots/ screenshots/
COPY Implementation_Documentation.md Example_Analyses.md Performance_Metrics.md README.md ./
COPY .gitattributes ./
COPY .env* ./

RUN mkdir -p logs outputs temp && chmod -R 777 logs outputs temp
RUN python generate_sample_image.py && python generate_screenshots.py

EXPOSE 7860

# Run Streamlit app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=7860", "--server.fileWatcherType=none", "--browser.gatherUsageStats=false"]
