FROM --platform=linux/x86_64 python:3.10-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    # uv is used for package management
    UV_VERSION=0.13.5

# System deps:
RUN python -m pip install --no-cache-dir "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70"
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