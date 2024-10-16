ARG PIP_DOWNLOAD_CACHE=/.cache/pip
ARG UV_CACHE_DIR=/.cache/uv
ARG SONAR_SCANNER_VERSION=6.2.1.4610

FROM ubuntu:24.04 AS base_image
RUN rm -f /etc/apt/apt.conf.d/docker-clean
COPY ci/docker/linux/jenkins/apt-packages.txt /tmp/
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    apt-get install -y software-properties-common gpg-agent --no-install-recommends && \
    add-apt-repository ppa:deadsnakes/ppa && \
    DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata --no-install-recommends && \
    apt-get update && \
     < /tmp/apt-packages.txt xargs apt-get install --no-install-recommends  -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


ARG PIP_DOWNLOAD_CACHE
ARG UV_CACHE_DIR
RUN mkdir -p ${PIP_DOWNLOAD_CACHE} && \
    chmod -R 777 ${PIP_DOWNLOAD_CACHE} && \
    mkdir -p ${UV_CACHE_DIR} && \
    chmod -R 777 ${UV_CACHE_DIR}

ENV UV_INDEX_STRATEGY=unsafe-best-match
