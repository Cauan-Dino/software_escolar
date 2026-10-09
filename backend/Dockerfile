# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.11.4 /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./

# Imagem com dependências de desenvolvimento: usada pelo serviço "tests" do compose.
FROM base AS dev
RUN uv sync --frozen
COPY . .
CMD ["pytest"]

# Imagem de execução da API.
FROM base AS prod
RUN uv sync --frozen --no-dev
COPY . .
RUN useradd --create-home appuser && mkdir -p /app/uploads && chown appuser /app/uploads
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
