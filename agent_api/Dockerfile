FROM python:3.13-slim-trixie AS builder

WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN uv pip install --no-cache-dir --upgrade pip
RUN uv pip install langgraph langchain mistralai chainlit langchain-mistralai httpx redis[hiredis] pydantic python-dotenv pyvips


FROM python:3.13-slim-trixie
RUN groupadd -r appuser && useradd -r -g appuser appuser

# libvips runtime library required by pyvips
RUN apt-get update && apt-get install -y --no-install-recommends libvips42 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=appuser:appuser . .

RUN apt-get update && apt-get install -y dos2unix && \
    find . -type f -exec dos2unix {} + && \
    apt-get purge -y dos2unix && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/uploads && \
    python -m compileall . && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8001

RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
