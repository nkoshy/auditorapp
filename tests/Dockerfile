FROM python:3.11-slim

WORKDIR /tests

RUN pip install --no-cache-dir \
    pytest==8.1.1 \
    httpx==0.27.0 \
    clickhouse-connect==0.7.16 \
    pytest-timeout==2.3.1

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["pytest", "e2e", "-v", "--tb=short", "--timeout=300"]
