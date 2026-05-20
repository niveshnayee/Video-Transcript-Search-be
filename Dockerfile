FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for ffmpeg/whisper/yt-dlp if needed (kept minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc ffmpeg git curl \
    && rm -rf /var/lib/apt/lists/*

# copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# copy app code
COPY . /app

EXPOSE 8000

CMD ["python", "run.py"]
