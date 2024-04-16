# Use official Docker Python 3.12 Alpine image as base image
FROM python:3.12-alpine AS base

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

# Set working directory and copy over app code
# N.B.: Use .dockerignore file exclusions to minimize image size
WORKDIR /app
COPY . /app

# Create and switch to new non-root user as best security practice

# Create a non-root user with an explicit UID and add permission to /app
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Run the application

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "main.py"]

# TODO: Module entry point
# ENTRYPOINT ["python", "-m", "orrery.simulator"]
