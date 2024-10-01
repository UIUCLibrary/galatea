ARG PIP_DOWNLOAD_CACHE=/.cache/pip
ARG UV_CACHE_DIR=/.cache/uv
ARG SONAR_SCANNER_VERSION=6.2.0.4584

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

FROM base_image AS SONAR_BUILDER
RUN apt-get update && \
    apt-get install --no-install-recommends -y unzip curl

ARG SONAR_SCANNER_VERSION
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar
RUN curl --create-dirs -sSLo /tmp/sonar-scanner.zip \
        https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-${SONAR_SCANNER_VERSION}-linux-x64.zip && \
    unzip -o /tmp/sonar-scanner.zip -d /opt/sonar/ && \
    rm /tmp/sonar-scanner.zip && \
    mkdir -p ${SONAR_USER_HOME}/cache && \
    chmod -R 777 "${SONAR_USER_HOME}"  &&  \
    ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    which sonar-scanner

FROM base_image

COPY --from=SONAR_BUILDER /opt/sonar /opt/sonar/
ARG SONAR_SCANNER_VERSION
ENV SONAR_SCANNER_VERSION=${SONAR_SCANNER_VERSION}
ARG SONAR_SCANNER_HOME=/opt/sonar/${SONAR_SCANNER_VERSION}-linux
ENV SONAR_USER_HOME=/opt/sonar/.sonar
RUN ln -s /opt/sonar/sonar-scanner-${SONAR_SCANNER_VERSION}-linux-x64/bin/sonar-scanner /usr/local/bin/sonar-scanner && \
    which sonar-scanner
RUN mkdir -p /home/user/.sonar/ && chmod -R 777 /home/user/

ARG PIP_DOWNLOAD_CACHE
ARG UV_CACHE_DIR
RUN mkdir -p ${PIP_DOWNLOAD_CACHE} && \
    chmod -R 777 ${PIP_DOWNLOAD_CACHE} && \
    mkdir -p ${UV_CACHE_DIR} && \
    chmod -R 777 ${UV_CACHE_DIR}

ENV UV_INDEX_STRATEGY=unsafe-best-match
