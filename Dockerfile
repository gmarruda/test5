# Stage 1: Install dependencies in a full Python environment
FROM python:3.11-slim-buster AS builder

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy application files
COPY . .

# Final Stage: Use the slim Python image directly (NO DISTROLESS)
FROM python:3.11-slim-buster

WORKDIR /app

# Copy the installed dependencies and application
COPY --from=builder /install /usr/local
COPY --from=builder /app .

EXPOSE 8000

CMD ["/usr/local/bin/python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
