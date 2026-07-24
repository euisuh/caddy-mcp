FROM python:3.12-slim

WORKDIR /app
RUN groupadd -r caddymcp && useradd -r -g caddymcp caddymcp
COPY pyproject.toml README.md LICENSE ./
COPY caddy_mcp ./caddy_mcp
RUN pip install --no-cache-dir .
USER caddymcp
CMD ["caddy-mcp"]
