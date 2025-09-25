FROM python:3.10-slim-buster AS builder
WORKDIR /app

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

COPY pyproject.toml uv.lock src ./
COPY .env .env

RUN uv pip install --all-features --requirement pyproject.toml

FROM python:3.10-slim-buster
WORKDIR /app

COPY --from=builder /root/.cargo/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv
COPY pyproject.toml uv.lock src ./
COPY .env .env

ENV PATH="/app/.venv/bin:$PATH"

CMD ["uv", "run", "-m", "src.main"]