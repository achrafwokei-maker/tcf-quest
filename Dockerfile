# Online beta image (Render free web service). Local development does not use this file.
# Stage 1: build the web app.
FROM node:22-slim AS web
WORKDIR /app/web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

# Stage 2: the API, serving the built web app. Data lives in Turso, AI in Cloudflare Workers AI.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    TCFQUEST_MODE=beta TCFQUEST_SERVE_WEB=1 TCFQUEST_DB_BACKEND=libsql TCFQUEST_AI_PROVIDER=workers
WORKDIR /app
COPY server/requirements-beta.txt server/
RUN pip install --no-cache-dir --require-hashes -r server/requirements-beta.txt
COPY server/tcfquest server/tcfquest
COPY content content
COPY --from=web /app/web/dist web/dist
RUN useradd --create-home app && mkdir -p data && chown app data
USER app
WORKDIR /app/server
# Secrets (Cloudflare, Turso, invite list, cookie key) come from Render's environment settings, never from git.
CMD ["sh", "-c", "exec python -m uvicorn tcfquest.main:app --host 0.0.0.0 --port ${PORT:-10000} --proxy-headers --forwarded-allow-ips='*'"]
