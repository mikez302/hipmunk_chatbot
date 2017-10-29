#!/usr/bin/env sh

python3 -m venv .
. bin/activate
export FLASK_APP=chatbot.py
flask run -p 9000 "$@"
