FROM python:3.13-slim

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DEFAULT_TIMEOUT=100 \
    DOCKER_APP_USERNAME=docker_app_user \
    DOCKER_USER_HOME=/home/docker_app_user

# Create User
RUN useradd --create-home --shell /bin/bash ${DOCKER_APP_USERNAME}

# Creating the workdir and fix permission for docker user
WORKDIR ${DOCKER_USER_HOME}/code
RUN chown -R ${DOCKER_APP_USERNAME}:${DOCKER_APP_USERNAME} ${DOCKER_USER_HOME}/code

# Switch to newly created user
USER $DOCKER_APP_USERNAME
ENV PATH="${DOCKER_USER_HOME}/.local/bin:${PATH}"

# Install poetry using pip
RUN pip install --upgrade pip
RUN pip install poetry

# Copy only requirements to cache them in docker layer
COPY --chown=${DOCKER_APP_USERNAME}:${DOCKER_APP_USERNAME} poetry.lock pyproject.toml ${DOCKER_USER_HOME}/code/

# Project initialization. Use prefix to avoid venv and custom path
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-ansi --no-root

# Adding the venv to path and copying the rest of the files
ENV PATH="${DOCKER_USER_HOME}/code/.venv/bin:${PATH}"
COPY --chown=${DOCKER_APP_USERNAME}:${DOCKER_APP_USERNAME} . ${DOCKER_USER_HOME}/code/