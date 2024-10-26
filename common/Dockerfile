FROM ubuntu:jammy-20240808

WORKDIR /app

COPY . /app

# Set cron job to run /app/scripts/cronscript.sh every 5 minutes
RUN apt-get update && apt-get install -y cron
RUN chmod +x /app/scripts/cronscript.sh

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Setup cron job
RUN (crontab -l ; echo "*/5 * * * * /app/scripts/cronscript.sh" >> /var/log/cron.log) | crontab

# Run the command on container startup
CMD cron && tail -f /var/log/cron.log
