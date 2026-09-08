FROM ghcr.io/astral-sh/uv:0.8.3 AS uv
FROM python:3.12-slim
COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 HF_HUB_DISABLE_TELEMETRY=1
RUN useradd --uid 10001 --create-home workbench && mkdir -p /app /home/workbench/models && chown workbench:workbench /app /home/workbench/models
WORKDIR /app
USER workbench
COPY --chown=workbench:workbench backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project
COPY --chown=workbench:workbench backend/ ./
EXPOSE 8000
CMD ["uv", "run", "--frozen", "uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
