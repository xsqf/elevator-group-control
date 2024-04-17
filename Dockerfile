# syntax=docker/dockerfile:1

# Use official Docker Python 3.12.2 Alpine image as base image
FROM python:3.12.2-alpine AS base

# Set up env

# Set locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Keep Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Set fault handler to enable Python tracebacks on segmentation faults
ENV PYTHONFAULTHANDLER 1

# Turn off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Start new build stage for installing Python dependencies, python-deps
FROM base AS python-deps

# Install pipenv
RUN pip install pipenv

# Install Python dependencies in new virtual environment
# N.B.: virtual env in project as a co-development-friendly practice
COPY Pipfile .
COPY Pipfile.lock .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

# Start new build stage for runtime image
FROM base AS runtime

# Copy virtual env from python-deps stage
COPY --from=python-deps /.venv /.venv
ENV PATH="/.venv/bin:$PATH"

# Set working directory
WORKDIR /elevator-group-control

# Transfer project code
# N.B.: Use .dockerignore file exclusions to minimize image size
COPY . /elevator-group-control

# Create and switch to new non-root user as best security practice

# Create a non-root user with an explicit UID and add needed permissions
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" egcuser && chown -R egcuser /elevator-group-control
USER egcuser

