FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml /app/
COPY src/ /app/src/
RUN pip install --no-cache-dir .
ENV SUS_STAGED_DATA=/data/staged SUS_USAGE_DB=/tmp/sus-usage.db PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "-m", "sus_health_mcp", "--http"]
