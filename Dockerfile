# Stage 1: Build
FROM python:3.11-slim AS builder

WORKDIR /app
COPY pyproject.toml .
COPY dezain/ dezain/

RUN pip install --no-cache-dir -e .

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Install Node.js for tsc validation (optional)
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && \
    rm -rf /var/lib/apt/lists/*

COPY samples/ samples/

ENTRYPOINT ["dezain"]
CMD ["generate", "--sample"]
