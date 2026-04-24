FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY uv.lock ./
COPY src ./src
COPY data ./data

RUN pip install --no-cache-dir pandas pymongo

CMD ["python", "src/migrate_validate.py"]