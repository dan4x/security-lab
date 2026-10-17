#!/usr/bin/env bash
# End-to-end demo: sets up the environment, starts the vulnerable app,
# runs the original exploit against it, and tears everything down.
#
# Exists so that anyone cloning this repo — or CI — can validate the whole
# lab with a single command, without any manual steps or guesswork about
# ports/timing.
#
# Usage: ./run_demo.sh
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

APP_PID=""
cleanup() {
    # Always stop the app, even if the exploit fails or the script is
    # interrupted — otherwise a stray process keeps port 4001 occupied.
    if [[ -n "$APP_PID" ]] && kill -0 "$APP_PID" 2>/dev/null; then
        kill "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

echo "[1/4] Setting up the virtual environment..."
if [[ ! -d .venv ]]; then
    python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

echo "[2/4] Generating the test database (challenge.db)..."
python3 make_fixture.py

echo "[3/4] Starting the vulnerable app on 127.0.0.1:4001..."
python3 app.py > /tmp/security-lab-app.log 2>&1 &
APP_PID=$!

# Poll instead of a fixed sleep: Flask's startup time varies by machine
# (slower on CI runners), so wait for the port to actually respond.
for _ in $(seq 1 30); do
    if curl -s -o /dev/null -m 1 "http://127.0.0.1:4001/api/user?username=admin"; then
        break
    fi
    sleep 0.2
done

echo "[4/4] Running the exploit..."
# Temporarily disable errexit: we need the exploit's real exit code (e.g.
# "flag not found" should fail the script), not have `set -e` kill the
# script before we can read $? and run cleanup.
set +e
python3 exploit_sqli_user.py
EXIT_CODE=$?
set -e

exit $EXIT_CODE
