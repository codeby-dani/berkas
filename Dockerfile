FROM python:3.13-slim

WORKDIR /app

# Dependencies first, so a code change does not re-resolve the world.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
# Shell form on purpose: Cloud Run injects $PORT at runtime.
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT}
