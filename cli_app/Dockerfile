# Interactive Presentation layer container build configuration
FROM python:3.11-slim

WORKDIR /app

# Copy dependency configuration
COPY requirements.txt .

# Install dependencies without local package registry caching to minimize size
RUN pip install --no-cache-dir -r requirements.txt

# Copy service source code
COPY cli_app/ /app/cli_app/

ENV PYTHONPATH=/app

# Run interactive bootstrap entrypoint
CMD ["python", "-m", "cli_app.main"]
