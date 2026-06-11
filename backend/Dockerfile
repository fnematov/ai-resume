FROM python:3.12-slim-bookworm

# uv for fast, reproducible installs
COPY --from=ghcr.io/astral-sh/uv:0.5.13 /uv /uvx /bin/

# System deps: LibreOffice (DOC/DOCX -> PDF) + curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install dependencies into the system environment (no project venv).
COPY pyproject.toml ./
RUN uv pip install --system \
        "fastapi>=0.115" "uvicorn[standard]>=0.32" "sqlalchemy[asyncio]>=2.0.36" "asyncpg>=0.30" \
        "alembic>=1.14" "pydantic>=2.10" "pydantic-settings>=2.6" "python-jose[cryptography]>=3.3" \
        "passlib[bcrypt]>=1.7.4" "bcrypt==4.0.1" "python-multipart>=0.0.17" "httpx>=0.28" \
        "celery[redis]>=5.4" "redis>=5.2" "cryptography>=44.0" "anthropic>=0.42" "openai>=1.59" \
        "pypdf>=5.1" "python-docx>=1.1" "pillow>=11.0" "email-validator>=2.2"

COPY . .
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["api"]
