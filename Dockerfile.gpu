# Stage 1: Build base with Python and base dependencies
FROM nvidia/cuda:12.6.0-runtime-ubuntu22.04 AS base-deps

ENV DEBIAN_FRONTEND=noninteractive

# Install system deps, Python 3.12, pip, and build essentials
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    tzdata \
    libgl1 \
    libglib2.0-0 \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 python3.12-dev python3.12-venv \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 \
    && python3.12 -m pip install --upgrade pip setuptools wheel

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

WORKDIR /app

COPY base-requirements.txt ./
RUN python -m pip install --no-cache-dir -r base-requirements.txt


# Stage 2: Final container with app code
FROM nvidia/cuda:12.6.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

# Repeat system + Python installation
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    tzdata \
    libgl1 \
    libglib2.0-0 \
    && ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime \
    && dpkg-reconfigure --frontend noninteractive tzdata \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.12 python3.12-dev python3.12-venv \
    && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 \
    && python3.12 -m pip install --upgrade pip setuptools wheel

# Set Python 3.12 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1

WORKDIR /app

# Copy base layer dependencies
COPY --from=base-deps /usr/local/lib/python3.12/dist-packages /usr/local/lib/python3.12/dist-packages
COPY --from=base-deps /usr/local/bin /usr/local/bin

# Install app requirements
COPY app-requirements.txt ./
RUN python -m pip install --no-cache-dir -r app-requirements.txt

# Copy code
COPY . .

EXPOSE 8000

RUN chmod +x entrypoint.sh

# Set entrypoint to download weights
ENTRYPOINT ["./entrypoint.sh"]

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]