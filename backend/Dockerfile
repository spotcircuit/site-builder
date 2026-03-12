FROM python:3.12-slim-bookworm

# Install Xvfb + Playwright system dependencies + Node.js (for React builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb xauth curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies
COPY pyproject.toml .
RUN uv sync --no-dev

# Install Chromium + all system deps (for Playwright scraping)
RUN uv run playwright install --with-deps chromium

# Pre-install React template node_modules for all 3 templates
COPY templates/react/package.json templates/react/package-lock.json* templates/react/
RUN cd templates/react && npm install --prefer-offline

COPY templates/react-bold/package.json templates/react-bold/package-lock.json* templates/react-bold/
RUN cd templates/react-bold && npm install --prefer-offline

COPY templates/react-elegant/package.json templates/react-elegant/package-lock.json* templates/react-elegant/
RUN cd templates/react-elegant && npm install --prefer-offline

COPY . .

# Railway provides $PORT at runtime
CMD xvfb-run --auto-servernum uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-9405}
# Railway deploy trigger 1773196554
