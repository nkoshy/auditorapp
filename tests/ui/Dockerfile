FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

WORKDIR /tests

RUN pip install --no-cache-dir \
    pytest==8.1.1 \
    pytest-playwright==0.5.1 \
    httpx==0.27.0 \
    pytest-timeout==2.3.1

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["pytest", "ui", "-v", "--tb=short", "--timeout=300", "--ignore=e2e"]
