#!/bin/bash
set -e

# Install dependencies
pip install --no-cache-dir -r requirements.txt

# Start Celery worker
exec celery -A okgbi worker -l info