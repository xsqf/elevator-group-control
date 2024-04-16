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

# Create and switch to new user as best security practice
RUN adduser --create-home appuser
WORKDIR /home/user
USER appuser

# Install application into container
# N.B.: Use .dockerignore file exclusions to minimize image size
COPY . .

# Run the application
ENTRYPOINT ["python", "-m", "http.server"]
CMD ["--directory", ".", "8000"]
