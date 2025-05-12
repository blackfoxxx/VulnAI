# Use an official Python runtime as a parent image for building
FROM python:3.9-slim AS builder

# Set working directory
WORKDIR /app

# Copy requirements.txt into the image
COPY requirements.txt requirements.txt

# Install system dependencies and Python dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# Create a Golang build stage
FROM golang:1.21-alpine AS go-builder

# Install git and necessary tools
RUN apk add --no-cache git build-base

# Install Nuclei
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# Install other Go-based security tools
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
RUN go install -v github.com/projectdiscovery/katana/cmd/katana@latest
RUN go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest
RUN go install -v github.com/lc/gau/v2/cmd/gau@latest

# Use a minimal image for the runtime
FROM python:3.9-slim AS runtime

# Set working directory
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Install required runtime dependencies for Golang tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    wget \
    unzip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Golang binaries from go-builder
COPY --from=go-builder /go/bin/nuclei /usr/local/bin/
COPY --from=go-builder /go/bin/subfinder /usr/local/bin/
COPY --from=go-builder /go/bin/httpx /usr/local/bin/
COPY --from=go-builder /go/bin/katana /usr/local/bin/
COPY --from=go-builder /go/bin/naabu /usr/local/bin/
COPY --from=go-builder /go/bin/gau /usr/local/bin/

# Copy the entire project
COPY . .

# Copy SSL certificates
COPY ssl/cert.pem /app/ssl/cert.pem
COPY ssl/key.pem /app/ssl/key.pem

# Create necessary directories and set permissions in one layer
RUN mkdir -p data/logs data/model && \
    adduser --disabled-password --gecos "" vulnuser && \
    chown -R vulnuser:vulnuser /app

# Switch to non-root user
USER vulnuser

# Expose the port for uvicorn
EXPOSE 8000

# Command to run the application with HTTPS
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/app/ssl/key.pem", "--ssl-certfile", "/app/ssl/cert.pem"]
