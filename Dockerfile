FROM --platform=linux/x86_64 python:3.10-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # uv is used for package management
    UV_VERSION=0.1.11

# System deps:
RUN pip install "uv==${UV_VERSION}"

WORKDIR /code

# Copy only pyproject.toml to leverage Docker layer caching.
COPY pyproject.toml ./

# Install dependencies using uv. The --system flag installs packages into the
# global site-packages, which is standard practice for containers.
RUN uv pip install . --system

# Copy the rest of the application code.
COPY . .

EXPOSE 8050

CMD ["python", "./hakai_qc_app/app.py"]