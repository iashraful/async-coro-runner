FROM python:3.13.7-alpine

COPY --from=ghcr.io/astral-sh/uv:0.8.14 /uv /uvx /bin/

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    TZ="Asia/Dhaka" \
    UV_LINK_MODE="copy" \
    APP_USERNAME="app_user" \
    USER_HOME="/home/app_user"

RUN apk add --no-cache \
    tzdata \
    bash \
    shadow \
    gcc \
    musl-dev \
    libffi-dev && \
    cp /usr/share/zoneinfo/Asia/Dhaka /etc/localtime && \
    echo "Asia/Dhaka" > /etc/timezone && \
    pip install --no-cache-dir --upgrade pip

RUN useradd --create-home --shell /bin/bash ${APP_USERNAME}

WORKDIR ${USER_HOME}/code
RUN chown -R ${APP_USERNAME}:${APP_USERNAME} ${USER_HOME}/code

USER ${APP_USERNAME}
ENV PATH="${USER_HOME}/.local/bin:${PATH}"

COPY --chown=${APP_USERNAME}:${APP_USERNAME} pyproject.toml uv.lock README.md ${USER_HOME}/code/

RUN uv pip install --prefix ${USER_HOME}/.local .
COPY --chown=${APP_USERNAME}:${APP_USERNAME} . ${USER_HOME}/code/