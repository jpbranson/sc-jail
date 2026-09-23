FROM python:3.13-slim@sha256:8d9d0b8bcf6506481eae4907c18f5e3e7902e629f5f6d684f9e7c32e85e3ddf0
ARG BUILD_REVISION=development
ENV SCJ_BUILD_REVISION=$BUILD_REVISION
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app
COPY requirements.lock requirements-build.lock ./
RUN pip install --no-cache-dir -r requirements.lock -r requirements-build.lock
COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir --no-deps --no-build-isolation . && useradd --uid 10001 --create-home app
USER app
EXPOSE 8080
CMD ["python", "-m", "sc_jail", "dashboard", "--host", "0.0.0.0", "--port", "8080"]
