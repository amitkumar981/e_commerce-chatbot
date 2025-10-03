FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (git only, minimal image size)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (leverage Docker layer caching)
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY prod_assistant ./prod_assistant
COPY . .

RUN pip install -e .

EXPOSE 8005

# Production (commented out)
# CMD ["bash", "-c", "python prod_assistant/mcp_servers/product_search_server.py & gunicorn prod_assistant.router.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 2 --timeout 120"]

# Local (runs MCP server + uvicorn with reload)
CMD ["bash", "-c", "python prod_assistant/mcp_servers/server.py & sleep 10 && uvicorn prod_assistant.router.main:app --host 0.0.0.0 --port 8005 --reload"]
