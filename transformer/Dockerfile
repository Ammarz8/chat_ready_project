# Cached build configuration for the transformer service
FROM python:3.11-slim

WORKDIR /app

# Copy python dependencies list from workspace context
COPY requirements.txt .

# Install dependencies without local package registry caching to minimize size
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code files
COPY transformer/ /app/transformer/

# Set Python search path to resolve module-level absolute imports correctly
ENV PYTHONPATH=/app

# Run service orchestrator main entrypoint
CMD ["python", "-m", "transformer.main"]
