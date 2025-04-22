FROM python:3.9-slim

WORKDIR /app

# Install git and other dependencies
RUN apt-get update && \
    apt-get install -y git cron procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Clone the repo directly (alternative to COPY)
RUN git clone https://github.com/Booza1981/iptv_logo_updater.git . || echo "Using build context instead"

# If cloning fails, copy from build context
COPY requirements.txt .
COPY *.py .
COPY *.txt .
COPY *.json .
COPY .env* .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/reports /data

# Create entrypoint script
RUN echo '#!/bin/bash' > /app/entrypoint.sh && \
    echo 'echo "Starting IPTV Logo Updater container"' >> /app/entrypoint.sh && \
    echo 'echo "Setting up cron job to run at: ${CRON_SCHEDULE:-15 0 * * *}"' >> /app/entrypoint.sh && \
    echo 'echo "${CRON_SCHEDULE:-15 0 * * *} cd /app && python update_channel_logos.py >> /var/log/cron.log 2>&1" > /etc/cron.d/logo-updater' >> /app/entrypoint.sh && \
    echo 'chmod 0644 /etc/cron.d/logo-updater' >> /app/entrypoint.sh && \
    echo 'crontab /etc/cron.d/logo-updater' >> /app/entrypoint.sh && \
    echo 'touch /var/log/cron.log' >> /app/entrypoint.sh && \
    echo 'echo "Container initialized. Running cron and waiting for scheduled execution..."' >> /app/entrypoint.sh && \
    echo 'cron && tail -f /var/log/cron.log' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Set entrypoint for container
ENTRYPOINT ["/app/entrypoint.sh"]
