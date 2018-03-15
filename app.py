from flask import Flask, url_for
import json
from datetime import date, datetime
app = Flask(__name__)

# https://stackoverflow.com/questions/13317536/get-a-list-of-all-routes-defined-in-the-app
def has_no_empty_params(rule):
  defaults = rule.defaults if rule.defaults is not None else ()
  arguments = rule.arguments if rule.arguments is not None else ()
  return len(defaults) >= len(arguments)


@app.route('/site')
def site():
  links = []
  for rule in app.url_map.iter_rules():
    if "GET" in rule.methods and has_no_empty_params(rule):
      url = url_for(rule.endpoint, **(rule.defaults or {}))
      links.append((url, rule.endpoint))
  return str(links)

@app.route('/time')
def time():
  return str(datetime.now())

@app.route('/hello/<hello>')
def hello(hello):
  return 'Hello ' + str(hello)
