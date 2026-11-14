# Stage 1: build the React app (frontend-app/ -> dist/)
FROM node:20-slim AS web
WORKDIR /web
COPY frontend-app/package.json frontend-app/package-lock.json ./
RUN npm ci --legacy-peer-deps --no-audit --no-fund
COPY frontend-app/ ./
RUN npm run build

# Stage 2: pipeline + API, serving the built app at "/"
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=web /web/dist ./frontend-app/dist
RUN python -m pipelines.orchestration.run_all
EXPOSE 8000
# PORT is set by Render / Railway / HF Spaces; 8000 locally. LLM keys come from the host's secret env vars, never the image.
# --proxy-headers: behind Render's proxy the AI rate limit sees each visitor's IP, not the proxy's.
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips '*'"]
