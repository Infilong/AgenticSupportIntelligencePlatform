FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.7.13 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1     UV_COMPILE_BYTECODE=1     UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
RUN uv pip install --system .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
