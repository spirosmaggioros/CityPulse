#!/bin/sh
set -e

# exec uvicorn chainlit_app:app \
    # --host 0.0.0.0 \
    # --port 8001 \
    # --workers 1

#!/bin/sh
set -e

# Default to redis:6379 if the environment variables are not set
REDIS_HOST=${REDIS_HOST}
REDIS_PORT=${REDIS_PORT}

echo "Waiting for Redis to start at $REDIS_HOST:$REDIS_PORT..."

# Wait loop using a Python socket check
while ! python -c "import socket; socket.create_connection(('$REDIS_HOST', $REDIS_PORT))" 2>/dev/null; do
  sleep 1
done

echo "Redis is up and ready!"
echo "Starting Chainlit..."

# Execute Chainlit with the recommended production flags
# Note: Replace 'chainlit_app.py' if your main file is named differently (e.g., 'app.py')
exec chainlit run agent.py \
    -h \
    --host 0.0.0.0 \
    --port 8001 \
    --root-path /chat