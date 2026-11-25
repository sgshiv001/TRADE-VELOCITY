FROM node:22-bookworm-slim AS frontend
WORKDIR /ui
ENV NEXT_TELEMETRY_DISABLED=1
COPY package.json pnpm-workspace.yaml pnpm-lock.yaml ./
COPY apps/web/package.json apps/web/package.json
COPY apps/desktop/package.json apps/desktop/package.json
COPY apps/mobile/package.json apps/mobile/package.json
COPY frontend/package.json frontend/package.json
COPY packages/client/package.json packages/client/package.json
RUN npm install -g pnpm@11.25.0 && pnpm --filter @tradevelocity/web... install --frozen-lockfile
COPY apps/web/ apps/web/
COPY frontend/ frontend/
COPY packages/client/ packages/client/
COPY src/stock_engine/data/market-history.json src/stock_engine/data/market-history.json
RUN pnpm --filter @tradevelocity/web build

FROM python:3.13-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 XDG_CACHE_HOME=/tmp/.cache
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[app,postgres,accounts]" && useradd --uid 10001 --create-home appuser && mkdir -p /data/sessions && chown -R appuser:appuser /data
COPY --from=frontend /ui/apps/web/out/ ./frontend/dist/
USER appuser
EXPOSE 8000
CMD ["python", "-m", "stock_engine.server"]
