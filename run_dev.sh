#!/usr/bin/env sh

python3 -m venv .
. bin/activate
export FLASK_APP=chatbot.py
export FLASK_DEBUG=1
flask run -p 9000 "$@"
