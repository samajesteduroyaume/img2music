# Use Python 3.11 base image
FROM python:3.11

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    ffmpeg \
    libsm6 \
    libxext6 \
    cmake \
    rsync \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && git lfs install

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
# IMPORTANT: Install Gradio 4.x BEFORE any Hugging Face packages
RUN pip install --no-cache-dir "gradio>=4.44.0,<5.0.0"

# Install other requirements
RUN pip install --no-cache-dir -r requirements.txt

# Install Hugging Face specific packages (but NOT gradio again)
RUN pip install --no-cache-dir \
    datasets \
    "huggingface-hub>=0.30" \
    "hf-transfer>=0.1.4" \
    "uvicorn>=0.14.0" \
    spaces

# Copy application code
COPY . .

# Create user directory
RUN mkdir -p /home/user && \
    ([ -e /home/user/app ] || ln -s /app/ /home/user/app) || true

# Expose port
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]
