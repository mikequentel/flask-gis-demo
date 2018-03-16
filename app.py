# pylint: disable=W0311
import os
from flask import Flask
from flask import url_for
from flask_cors import CORS
import json
from geographiclib.geodesic import Geodesic
from geopy.distance import vincenty
from datetime import date, datetime
import math
import urllib
import psycopg2
from psycopg2.extras import RealDictCursor
app = Flask(__name__)
CORS(app)
DB_URL = os.getenv('DB_URL', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'businesses')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWD = os.getenv('DB_PASSWD', 'postgres')

# conn_string = "host='localhost' dbname='businesses' user='postgres' password='postgres'"
conn_string = "host=%s dbname=%s user=%s password=%s" % (DB_URL, DB_NAME, DB_USER, DB_PASSWD)
conn = psycopg2.connect(conn_string)

# https://stackoverflow.com/questions/13317536/get-a-list-of-all-routes-defined-in-the-app
def has_no_empty_params(rule):
  defaults = rule.defaults if rule.defaults is not None else ()
  arguments = rule.arguments if rule.arguments is not None else ()
  return len(defaults) >= len(arguments)

# https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable
def json_serial(obj):
  if isinstance(obj, (datetime, date)):
    return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))

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

@app.route('/restaurants/limit/<limit>', methods=['GET'])
def limit(limit):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  limit = long(urllib.unquote(limit))
  sql = "SELECT * FROM restaurants LIMIT %s"
  query = cursor.mogrify(sql, (limit, ))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/oid/<oid>', methods=['GET'])
def oid(oid):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  oid = long(urllib.unquote(oid))
  sql = "SELECT * FROM restaurants WHERE oid = %s"
  query = cursor.mogrify(sql, (oid, ))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/bbox/<bbox>', methods=['GET'])
def bbox(bbox):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  bbox = urllib.unquote(bbox)
  print bbox
  coords = bbox.split(",")
  top = float(coords[0])
  left = float(coords[1])
  bottom = float(coords[2])
  right = float(coords[3])
  sql = "SELECT * FROM restaurants WHERE (latitude BETWEEN %s AND %s) AND (longitude BETWEEN %s AND %s)"
  query = cursor.mogrify(sql, (bottom, top, left, right))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/circle/<circle>', methods=['GET'])
def circle(circle):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  circle = urllib.unquote(circle)
  print circle
  coords = circle.split(",")
  centre_lat = float(coords[0])
  centre_lon = float(coords[1])
  # radius input is in km but needs to be converted to metres for geographiclib
  radius = float(coords[2]) * 1000.0
  # Step 1: determine bounding box of outer circle.
  # NOTE: geographiclib expects azimuths (bearings) relative to true north (where north is zero).
  geod = Geodesic.WGS84
  north_bounding_point = geod.Direct(centre_lat, centre_lon, 0, radius)
  south_bounding_point = geod.Direct(centre_lat, centre_lon, 180, radius)
  east_bounding_point = geod.Direct(centre_lat, centre_lon, 90, radius)
  west_bounding_point = geod.Direct(centre_lat, centre_lon, 270, radius)
  sql = "SELECT * FROM restaurants WHERE (latitude BETWEEN %s AND %s) AND (longitude BETWEEN %s AND %s)"
  query = cursor.mogrify(sql, (south_bounding_point['lat2'], north_bounding_point['lat2'], west_bounding_point['lon2'], east_bounding_point['lon2']))
  print query
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  # Step 2: iterate through records in bounding box, comparing each distance to radius, selecting whatever is within that distance.
  items_within_circle = []
  for rec in records:
    # Just as geographiclib uses metres, here, for consistency, use metres as well in geopy
    dist = vincenty((centre_lat, centre_lon), (rec['latitude'], rec['longitude'])).m
    if dist < radius:
      items_within_circle.append(rec)
  return json.dumps(items_within_circle, default=json_serial)

@app.route('/restaurants/address/<address>')
def address(address):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  address = urllib.unquote(address)
  sql = "SELECT * FROM restaurants WHERE address = %s"
  query = cursor.mogrify(sql, (address,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/county/<county>', methods=['GET'])
def county(county):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  county = urllib.unquote(county)
  sql = "SELECT * FROM restaurants WHERE county = %s"
  query = cursor.mogrify(sql, (county,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/critical_violation/<critical_violation>')
def critical_violation(critical_violation):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  critical_violation = urllib.unquote(critical_violation)
  sql = "SELECT * FROM restaurants WHERE critical_violation = %s"
  query = cursor.mogrify(sql, (critical_violation,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/date_of_inspection/<date_of_inspection>')
def date_of_inspection(date_of_inspection):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  date_of_inspection = urllib.unquote(date_of_inspection)
  sql = "SELECT * FROM restaurants WHERE date_of_inspection = %s"
  query = cursor.mogrify(sql, (date_of_inspection,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/facility/<facility>')
def facility(facility):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  facility = urllib.unquote(facility)
  sql = "SELECT * FROM restaurants WHERE facility = %s"
  query = cursor.mogrify(sql, (facility,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/facility_address/<facility_address>')
def facility_address(facility_address):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  facility_address = urllib.unquote(facility_address)
  sql = "SELECT * FROM restaurants WHERE facility_address = %s"
  query = cursor.mogrify(sql, (facility_address,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/facility_city/<facility_city>')
def facility_city(facility_city):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  facility_city = urllib.unquote(facility_city)
  sql = "SELECT * FROM restaurants WHERE facility_city = %s"
  query = cursor.mogrify(sql, (facility_city,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/facility_code/<facility_code>')
def facility_code(facility_code):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  facility_code = urllib.unquote(facility_code)
  sql = "SELECT * FROM restaurants WHERE facility_code = %s"
  query = cursor.mogrify(sql, (facility_code,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/facility_municipality/<facility_municipality>')
def facility_municipality(facility_municipality):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  facility_municipality = urllib.unquote(facility_municipality)
  sql = "SELECT * FROM restaurants WHERE facility_municipality = %s"
  query = cursor.mogrify(sql, (facility_municipality,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/facility_postal_zipcode/<facility_postal_zipcode>')
def facility_postal_zipcode(facility_postal_zipcode):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  facility_postal_zipcode = urllib.unquote(facility_postal_zipcode)
  sql = "SELECT * FROM restaurants WHERE facility_postal_zipcode = %s"
  query = cursor.mogrify(sql, (facility_postal_zipcode,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/food_service_description/<food_service_description>')
def food_service_description(food_service_description):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  food_service_description = urllib.unquote(food_service_description)
  sql = "SELECT * FROM restaurants WHERE food_service_description = %s"
  query = cursor.mogrify(sql, (food_service_description,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/food_service_type/<food_service_type>')
def food_service_type(food_service_type):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  food_service_type = urllib.unquote(food_service_type)
  sql = "SELECT * FROM restaurants WHERE food_service_type = %s"
  query = cursor.mogrify(sql, (food_service_type,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/fs_facility_state/<fs_facility_state>')
def fs_facility_state(fs_facility_state):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  fs_facility_state = urllib.unquote(fs_facility_state)
  sql = "SELECT * FROM restaurants WHERE fs_facility_state = %s"
  query = cursor.mogrify(sql, (fs_facility_state,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/inspection_comments/<inspection_comments>')
def inspection_comments(inspection_comments):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  inspection_comments = urllib.unquote(inspection_comments)
  sql = "SELECT * FROM restaurants WHERE inspection_comments = %s"
  query = cursor.mogrify(sql, (inspection_comments,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/inspection_type/<inspection_type>')
def inspection_type(inspection_type):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  inspection_type = urllib.unquote(inspection_type)
  sql = "SELECT * FROM restaurants WHERE inspection_type = %s"
  query = cursor.mogrify(sql, (inspection_type,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/inspector_id/<inspector_id>')
def inspector_id(inspector_id):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  inspector_id = urllib.unquote(inspector_id)
  sql = "SELECT * FROM restaurants WHERE inspector_id = %s"
  query = cursor.mogrify(sql, (inspector_id,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/latitude/<latitude>')
def latitude(latitude):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  latitude = urllib.unquote(latitude)
  sql = "SELECT * FROM restaurants WHERE latitude = %s"
  query = cursor.mogrify(sql, (latitude,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/local_health_department/<local_health_department>')
def local_health_department(local_health_department):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  local_health_department = urllib.unquote(local_health_department)
  sql = "SELECT * FROM restaurants WHERE local_health_department = %s"
  query = cursor.mogrify(sql, (local_health_department,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/longitude/<longitude>')
def longitude(longitude):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  longitude = urllib.unquote(longitude)
  sql = "SELECT * FROM restaurants WHERE longitude = %s"
  query = cursor.mogrify(sql, (longitude,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/nysdoh_gazetteer_1980/<nysdoh_gazetteer_1980>')
def nysdoh_gazetteer_1980(nysdoh_gazetteer_1980):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  nysdoh_gazetteer_1980 = urllib.unquote(nysdoh_gazetteer_1980)
  sql = "SELECT * FROM restaurants WHERE nysdoh_gazetteer_1980 = %s"
  query = cursor.mogrify(sql, (nysdoh_gazetteer_1980,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/nys_health_operation_id/<nys_health_operation_id>')
def nys_health_operation_id(nys_health_operation_id):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  nys_health_operation_id = urllib.unquote(nys_health_operation_id)
  sql = "SELECT * FROM restaurants WHERE nys_health_operation_id = %s"
  query = cursor.mogrify(sql, (nys_health_operation_id,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/operation_name/<operation_name>')
def operation_name(operation_name):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  operation_name = urllib.unquote(operation_name)
  sql = "SELECT * FROM restaurants WHERE operation_name = %s"
  query = cursor.mogrify(sql, (operation_name,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/permit_expiration_date/<permit_expiration_date>')
def permit_expiration_date(permit_expiration_date):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  permit_expiration_date = urllib.unquote(permit_expiration_date)
  sql = "SELECT * FROM restaurants WHERE permit_expiration_date = %s"
  query = cursor.mogrify(sql, (permit_expiration_date,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/permitted_corp_name/<permitted_corp_name>')
def permitted_corp_name(permitted_corp_name):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  permitted_corp_name = urllib.unquote(permitted_corp_name)
  sql = "SELECT * FROM restaurants WHERE permitted_corp_name = %s"
  query = cursor.mogrify(sql, (permitted_corp_name,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/permitted_dba/<permitted_dba>')
def permitted_dba(permitted_dba):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  permitted_dba = urllib.unquote(permitted_dba)
  sql = "SELECT * FROM restaurants WHERE permitted_dba = %s"
  query = cursor.mogrify(sql, (permitted_dba,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/perm_operator_first_name/<perm_operator_first_name>')
def perm_operator_first_name(perm_operator_first_name):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  perm_operator_first_name = urllib.unquote(perm_operator_first_name)
  sql = "SELECT * FROM restaurants WHERE perm_operator_first_name = %s"
  query = cursor.mogrify(sql, (perm_operator_first_name,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/perm_operator_last_name/<perm_operator_last_name>')
def perm_operator_last_name(perm_operator_last_name):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  perm_operator_last_name = urllib.unquote(perm_operator_last_name)
  sql = "SELECT * FROM restaurants WHERE perm_operator_last_name = %s"
  query = cursor.mogrify(sql, (perm_operator_last_name,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/total_num_critical_violations/<total_num_critical_violations>')
def total_num_critical_violations(total_num_critical_violations):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  total_num_critical_violations = urllib.unquote(total_num_critical_violations)
  sql = "SELECT * FROM restaurants WHERE total_num_critical_violations = %s"
  query = cursor.mogrify(sql, (total_num_critical_violations,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/total_num_crit_not_corrected/<total_num_crit_not_corrected>')
def total_num_crit_not_corrected(total_num_crit_not_corrected):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  total_num_crit_not_corrected = urllib.unquote(total_num_crit_not_corrected)
  sql = "SELECT * FROM restaurants WHERE total_num_crit_not_corrected = %s"
  query = cursor.mogrify(sql, (total_num_crit_not_corrected,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/total_num_noncritical_violations/<total_num_noncritical_violations>')
def total_num_noncritical_violations(total_num_noncritical_violations):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  total_num_noncritical_violations = urllib.unquote(total_num_noncritical_violations)
  sql = "SELECT * FROM restaurants WHERE total_num_noncritical_violations = %s"
  query = cursor.mogrify(sql, (total_num_noncritical_violations,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/violation_description/<violation_description>')
def violation_description(violation_description):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  violation_description = urllib.unquote(violation_description)
  sql = "SELECT * FROM restaurants WHERE violation_description = %s"
  query = cursor.mogrify(sql, (violation_description,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)

@app.route('/restaurants/violation_item/<violation_item>')
def violation_item(violation_item):
  cursor = conn.cursor(cursor_factory=RealDictCursor)
  violation_item = urllib.unquote(violation_item)
  sql = "SELECT * FROM restaurants WHERE violation_item = %s"
  query = cursor.mogrify(sql, (violation_item,))
  cursor.execute(query)
  records = cursor.fetchall()
  cursor.close()
  return json.dumps(records, default=json_serial)
