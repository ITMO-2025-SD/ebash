FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

RUN pip install --upgrade pip && \
    pip install uv pytest

COPY . .
RUN uv pip install --system -e .

ENV PYTHONPATH=/app

CMD ["python", "main.py"]
