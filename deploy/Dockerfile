FROM node:22-bookworm-slim AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 XDG_CACHE_HOME=/tmp/.cache
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[app]" && useradd --uid 10001 --create-home appuser && mkdir -p /data/sessions && chown -R appuser:appuser /data
COPY --from=frontend /ui/dist/ ./frontend/dist/
USER appuser
EXPOSE 8000
CMD ["python", "-m", "stock_engine.server"]
