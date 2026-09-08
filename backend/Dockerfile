FROM ghcr.io/astral-sh/uv:0.8.3 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project
COPY backend/ ./
RUN useradd --uid 10001 --create-home workbench && chown -R workbench:workbench /app
USER workbench
EXPOSE 8000
CMD ["uv", "run", "--frozen", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
