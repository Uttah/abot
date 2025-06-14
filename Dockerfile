FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
  PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY src/ ./src

RUN pip install --no-cache-dir aiogram aiosqlite python-dotenv

CMD ["python", "-u", "-m", "src"]
