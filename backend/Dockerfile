FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . ./backend

ENV PYTHONPATH=/app
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "backend.gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
