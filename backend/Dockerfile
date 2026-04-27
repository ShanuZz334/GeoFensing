FROM python:3.11-slim

# System deps for dlib + face_recognition native build
RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    wget \
    bzip2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
RUN pip install --no-cache-dir dlib==19.24.4
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Model provided via volume mount
RUN mkdir -p models

# Copy application
COPY . .

EXPOSE 5000

CMD ["gunicorn", "--config", "gunicorn.conf.py", "run:app"]
