# Use official Docker Python 3.12 slimmed image as base image
FROM 3.12-slim AS base

# Set up env

# Set locale
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Set so that source modules won't try to write .pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# Set fault handler to enable Python tracebacks on segfaults
ENV PYTHONFAULTHANDLER 1

# Set to turn off buffering for easier container logging
# ENV PYTHONUNBUFFERED 1

# Start new build stage for installing Python dependencies, python-deps
FROM base AS python-deps

# Install pipenv and compilation dependencies
# N.B.: gcc for compilation dependencies might not be required
RUN pip install pipenv
RUN apt-get update && apt-get install -y --no-install-recommends gcc

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
RUN useradd --create-home appuser
WORKDIR /home/user
USER appuser

# Install application into container
# N.B.: Use .dockerignore file exclusions to minimize image size
COPY . .

# Run the application
ENTRYPOINT ["python", "-m", "http.server"]
CMD ["--directory", ".", "8000"]
