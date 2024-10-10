#!/bin/bash

# Variables
HEALTH_CHECK_URL="http://localhost:8000/healthcheck"
EMAIL_TO="jluar@precisioninno.com"
EMAIL_SUBJECT="Web App Health Check Failed"
EMAIL_BODY="The health check endpoint is down or unreachable: $HEALTH_CHECK_URL"
LOG_FILE="/var/log/webapp_health_check.log"
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Perform health check
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}" "$HEALTH_CHECK_URL")

# If the status code is not 200, send an email and log the failure
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "$TIMESTAMP - Health check failed. Status code: $HTTP_STATUS" >> $LOG_FILE
    echo "$EMAIL_BODY" | mail -s "$EMAIL_SUBJECT" "$EMAIL_TO"
else
    echo "$TIMESTAMP - Health check succeeded. Status code: $HTTP_STATUS" >> $LOG_FILE
fi
