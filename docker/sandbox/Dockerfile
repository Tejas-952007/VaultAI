# Dockerfile for minimal sandbox image
# Uses official python slim image, runs as non-root user
FROM python:3.12-slim

# Create non-root user (uid 1000)
RUN adduser --uid 1000 --disabled-password --gecos "" sandboxuser

# Set working directory
WORKDIR /app

# Copy only needed files (none needed for execution)
# No additional packages installed

# Switch to non-root user
USER sandboxuser

# Entry point is python interpreter
ENTRYPOINT ["python"]
