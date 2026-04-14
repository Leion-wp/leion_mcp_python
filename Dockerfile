FROM python:3.11-slim

WORKDIR /app

# System deps (needed by mcp-git)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install project + deps
# Phase D.0.2: Add redis[hiredis] for Backend event streaming
RUN pip install --no-cache-dir -e . redis[hiredis]>=7.1.0 structlog>=25.0.0

# FastMCP servers will bind to these ports (router + workers)
EXPOSE 7000 7001 7002 7003 7004 7005 7006 7007 7008 7009 7010

CMD ["bash"]
