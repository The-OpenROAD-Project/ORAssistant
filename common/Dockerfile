FROM ubuntu:jammy-20240808

WORKDIR /app

COPY . /app

# Set cron job to run /app/scripts/cronscript.sh every 5 minutes
RUN apt-get update && apt-get install -y cron
RUN chmod +x /app/scripts/cronscript.sh
RUN crontab -l | {cat; echo "*/5 * * * * /app/scripts/cronscript.sh" } | crontab -

CMD ["cron", "-f"]
