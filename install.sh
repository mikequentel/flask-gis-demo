#!/bin/bash
NAME=$1
if [ -z "${NAME}" ]; then
  echo "Include name of project."
  exit 1
fi

if [ ! -d ~/.virtualenvs/${NAME} ]; then
  virtualenv --python $(which python) ~/.virtualenvs/$NAME
fi
source ~/.virtualenvs/$NAME/bin/activate
pip install Flask
cat << EOF >> app.py
from flask import Flask
import json
from datetime import date, datetime
app = Flask(__name__)

@app.route('/introspect')
def introspect():
  return app.current_request.to_dict()

@app.route('/time')
def time():
  return str(datetime.now())

EOF

pip freeze > requirements.txt

export FLASK_APP=app.py
flask run
