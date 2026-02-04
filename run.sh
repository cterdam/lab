#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<EOF
Usage: $0 [OPTIONS] [TARGET]

Launch Docker containers for the lab environment.

TARGET:
    app     Run the main application (default)
    test    Run the test suite

OPTIONS:
    -p, --port PORT    Redis UI port on host (default: 8001)
    -n, --name NAME    Project name suffix for isolation (default: random)
    -h, --help         Show this help message

EXAMPLES:
    $0                      # Run app on port 8001
    $0 test                 # Run tests on port 8001
    $0 -p 8002              # Run app on port 8002
    $0 -p 8002 -n dev test  # Run tests on port 8002 with project name lab-dev

For concurrent runs, use different ports:
    $0 -p 8001 -n run1 &
    $0 -p 8002 -n run2 &
EOF
}

# Defaults
PORT=8001
NAME="$(head -c 4 /dev/urandom | xxd -p)"
TARGET="app"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -n|--name)
            NAME="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        app|test)
            TARGET="$1"
            shift
            ;;
        *)
            echo "Error: Unknown option $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

export COMPOSE_PROJECT_NAME="lab-${NAME}"
export REDIS_UI_PORT="${PORT}"

cd "$(dirname "$0")"

cleanup() {
    docker compose down -v >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

echo "Starting ${TARGET} (project: ${COMPOSE_PROJECT_NAME}, Redis UI: http://localhost:${PORT})"
docker compose up --build "${TARGET}" -d --quiet-pull >/dev/null 2>&1
docker logs -f "$(docker compose ps -q "${TARGET}")"
