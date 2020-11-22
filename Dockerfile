ARG PYTHON_VERSION
FROM python:${PYTHON_VERSION}
LABEL vendor="dProg - Philippe Docourt" maintainer="Philippe Docourt" description="Demo Site for Django QR code"

ENV PYTHONUNBUFFERED 1

# Set env variables used in this Dockerfile (add a unique prefix, such as <app name>)
# Directory in container for project source files.
ARG APP_BASE_DIR=/usr/src/app

# Declare a proper Django settings file.
ENV DJANGO_SETTINGS_MODULE=demo_site.settings

# Make app dir.
RUN mkdir -p "$APP_BASE_DIR"
WORKDIR "$APP_BASE_DIR"

# Install requirements (separate step for caching intermediate image).
COPY requirements.txt "$APP_BASE_DIR/"
RUN pip install -r requirements.txt
COPY requirements-web-deployment.txt "$APP_BASE_DIR/"
RUN pip install -r requirements-web-deployment.txt

# Copy entrypoint script into the image.
COPY ./docker-entrypoint.sh /

# Invoke app's entrypoint via dumb-init so that sub-processes are handled properly.
CMD ["/docker-entrypoint.sh"]
