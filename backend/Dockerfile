FROM python:3.11-slim AS builder

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv pip install --system -r pyproject.toml || pip install fastapi uvicorn pydantic pydantic-settings sqlalchemy alembic aiosqlite httpx litellm pyyaml python-multipart websockets cryptography

FROM python:3.11-slim

RUN groupadd -r polyspace && useradd -r -g polyspace polyspace

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN mkdir -p /app/data && chown -R polyspace:polyspace /app

USER polyspace

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
