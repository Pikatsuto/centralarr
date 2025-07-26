FROM debian:bookworm

# Basic environment variables
ENV PORT=5000 \
    FLASK_ENV=prod \
    APP_DIR=/opt/centralarr \
    DB_PATH=/opt/centralarr/db/centralarr.db

# Installing dependencies for Python and Gunicorn
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv gunicorn && \
    apt-get clean

# Copy and install your .deb (build externally then copy here)
COPY makedeb/output/centralarr_*.deb /tmp/
RUN dpkg -i /tmp/centralarr_*.deb || apt-get install -f -y

# Creation of the folder for the DB (volume declared below)
RUN mkdir -p /opt/centralarr/db

# Expose the port (default 5000)
EXPOSE ${PORT}

# Volume for the SQLite database (persistence)
VOLUME ["/opt/centralarr/db"]

# Basic health check: ping the main API
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT}/api/health || exit 1

WORKDIR /opt/centralarr

CMD ["uvicorn", "main:create_app", "--host", "0.0.0.0", "--port", "${PORT}", "--factory"]