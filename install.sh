#!/bin/sh
# Install only; never starts a capture or paper session.
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$project_dir"
python3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12), "Python 3.12 required"'
if [ ! -d .venv ]; then
    python3.12 -m venv .venv
fi
.venv/bin/python -c 'import sys; assert sys.version_info[:2] == (3, 12), "Existing .venv must use Python 3.12"'
.venv/bin/python -m pip install --disable-pip-version-check --no-deps --require-hashes -r crypto_paper/requirements.lock
.venv/bin/python -m pip check
.venv/bin/python -c 'import websockets; assert websockets.__version__ == "15.0.1"'
printf '%s\n' 'Installation complete. Use .venv/bin/python -m crypto_paper --help'
