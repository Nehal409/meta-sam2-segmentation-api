#!/bin/bash

set -e

echo "Running database migrations..."
alembic upgrade head
echo "Migrations completed."

echo "Downloading model weights..."
python scripts/download_weights.py
echo "Weights ready."

# Call whatever command was passed (i.e., CMD)
exec "$@"
